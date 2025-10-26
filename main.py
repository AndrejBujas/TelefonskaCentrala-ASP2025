import os
import time
import pickle
import threading
import random
from datetime import datetime
from difflib import SequenceMatcher

from graph import Graph
from trie import PhoneBookTrie


graph = Graph()
phonebook_trie = PhoneBookTrie()
blokirani_brojevi = set()
kontakti = {}  # broj -> {ime, prezime, puno_ime, original_broj}


# ===== HELPER FUNKCIJE =====

def normalizuj_broj(broj):
    if isinstance(broj, str):
        return broj.replace(" ", "").replace("-", "")
    return str(broj)


def validan_broj(broj):
    return broj and broj.isdigit()


def parsiraj_trajanje(trajanje_str):
    try:
        parts = trajanje_str.split(':')
        if len(parts) == 3:
            sati, minuti, sekunde = map(int, parts)
            return sati * 3600 + minuti * 60 + sekunde
    except:
        pass
    return 0


def formatiraj_trajanje(sekunde):
    sati = int(sekunde // 3600)
    minuti = int((sekunde % 3600) // 60)
    sek = int(sekunde % 60)
    return f"{sati:02d}:{minuti:02d}:{sek:02d}"


def get_kontakt_info(broj):
    if broj in kontakti:
        info = kontakti[broj]
        return f"{info['puno_ime']} ({info['original_broj']})"
    return broj


def autocomplete_input(prompt, tip='broj'):

    while True:
        unos = input(prompt).strip()

        if unos.endswith('*'):
            prefiks = unos[:-1]

            if not prefiks:
                print("Unesite bar jedan karakter pre * za autocomplete")
                continue

            if tip == 'broj':
                sugestije = phonebook_trie.autocomplete_phone(prefiks, max_suggestions=5)
            elif tip == 'ime':
                sugestije = phonebook_trie.autocomplete_first_name(prefiks, max_suggestions=5)
            else:
                sugestije = phonebook_trie.autocomplete_last_name(prefiks, max_suggestions=5)

            if not sugestije:
                print(f"Nema sugestija za '{prefiks}'")
                continue


            print(f"\nSugestije za {prefiks}:")
            for i, (text, data) in enumerate(sugestije, 1):
                if tip == 'broj':
                    ime = data.get('first_name', '')
                    prezime = data.get('last_name', '')
                    print(f"  {i}. {text} - {ime} {prezime}")
                else:
                    print(f"  {i}. {text}")

            izbor = input("\nIzaberite broj (Enter za ponovni unos): ").strip()
            if izbor.isdigit():
                idx = int(izbor) - 1
                if 0 <= idx < len(sugestije):
                    return sugestije[idx][0]

            continue

        return unos


# ===== UCITAVANJE I CUVANJE PODATAKA =====

def ucitaj_kontakte(filename='phones.txt'):

    print(f"Ucitavanje kontakata iz {filename}")

    with open(filename, 'r', encoding='utf-8') as f:
        next(f)
        for line in f:
            line = line.strip()
            if not line:
                continue

            parts = line.split(',')
            if len(parts) >= 2:
                ime_prezime = parts[0].strip()
                broj = parts[1].strip()

                # Razdvoji ime i prezime
                name_parts = ime_prezime.split()
                if len(name_parts) >= 2:
                    ime = name_parts[0]
                    prezime = ' '.join(name_parts[1:])
                else:
                    ime = ime_prezime
                    prezime = ""

                normalizovan_broj = normalizuj_broj(broj)

                phonebook_trie.add_contact(normalizovan_broj, ime, prezime)

                graph.add_phone(normalizovan_broj)

                kontakti[normalizovan_broj] = {
                    'ime': ime,
                    'prezime': prezime,
                    'puno_ime': ime_prezime,
                    'original_broj': broj
                }

    print(f"Učitano {len(kontakti)} kontakata.")


def ucitaj_blokirane(filename='blocked.txt'):

    if not os.path.exists(filename):
        print(f"UPOZORENJE: Fajl {filename} ne postoji!")
        return

    print(f"Ucitavanje blokiranih brojeva iz {filename}...")

    with open(filename, 'r', encoding='utf-8') as f:
        for line in f:
            broj = line.strip()
            if broj:
                normalizovan = normalizuj_broj(broj)
                blokirani_brojevi.add(normalizovan)

    print(f"Ucitano {len(blokirani_brojevi)} blokiranih brojeva.")


def ucitaj_pozive(filename='calls.txt', max_poziva=None):

    if not os.path.exists(filename):
        print(f"UPOZORENJE: Fajl {filename} ne postoji! Pokrenite generate_calls.py prvo.")
        return

    print(f"Učitavanje poziva iz {filename}...")
    if max_poziva:
        print(f"(učitavanje prvih {max_poziva} poziva)")

    pozivi_ucitani = 0
    pozivi_blokirani = 0

    with open(filename, 'r', encoding='utf-8') as f:
        for line in f:
            if max_poziva and pozivi_ucitani >= max_poziva:
                break

            line = line.strip()
            if not line:
                continue

            parts = [p.strip() for p in line.split(',')]
            if len(parts) >= 4:
                caller = normalizuj_broj(parts[0])
                callee = normalizuj_broj(parts[1])
                datum_vreme = parts[2]
                trajanje = parts[3]

                # Proveri validnost
                if not validan_broj(caller) or not validan_broj(callee):
                    continue

                # NE blokiraj istorijske pozive, ali ih broji
                if caller in blokirani_brojevi or callee in blokirani_brojevi:
                    pozivi_blokirani += 1

                # Parsiraj vreme
                try:
                    timestamp = datetime.strptime(datum_vreme, '%d.%m.%Y %H:%M:%S')
                except:
                    timestamp = datetime.now()

                # Parsiraj trajanje
                trajanje_sek = parsiraj_trajanje(trajanje)


                graph.add_call(caller, callee, trajanje_sek, timestamp)
                pozivi_ucitani += 1

                if pozivi_ucitani % 10000 == 0:
                    print(f"  Učitano {pozivi_ucitani} poziva...")

    print(f"Učitano {pozivi_ucitani} poziva (od toga {pozivi_blokirani} sa blokiranim brojevima)")


def sacuvaj_pickle(filename='centrala_data.pkl'):
    print(f"\nCuvanje podataka u {filename}...")

    data = {
        'graph': graph,
        'phonebook_trie': phonebook_trie,
        'blokirani_brojevi': blokirani_brojevi,
        'kontakti': kontakti
    }

    with open(filename, 'wb') as f:
        pickle.dump(data, f)

    print("Podaci uspešno sacuvani!")


def ucitaj_pickle(filename='centrala_data.pkl'):
    global graph, phonebook_trie, blokirani_brojevi, kontakti

    if not os.path.exists(filename):
        return False

    print(f"Ucitavanje podataka iz {filename}...")

    try:
        with open(filename, 'rb') as f:
            data = pickle.load(f)

        graph = data['graph']
        phonebook_trie = data['phonebook_trie']
        blokirani_brojevi = data['blokirani_brojevi']
        kontakti = data['kontakti']

        print("Podaci uspešno ucitani")
        return True

    except Exception as e:
        print(f"Greksa pri ucitavanju: {e}")
        return False


def simulacija_pozivanja_uzivo():
    print("Simulacija pozivanja uzivo")
    print("=" * 80)
    print("Dodajte * na kraju broja za autocomplete (npr: 064*)")

    # Unos pozivaoca
    caller = autocomplete_input("\nUnesite broj pozivaoca: ", tip='broj')
    caller_norm = normalizuj_broj(caller)

    if not validan_broj(caller_norm):
        print("Neispravan broj pozivaoca!")
        return

    if caller_norm in blokirani_brojevi:
        print(f"Broj {caller} je blokiran")
        return

    if caller_norm not in kontakti:
        print(f"\n Broj {caller_norm} ne postoji u imeniku.")

        sugestije = did_you_mean(caller_norm)
        if sugestije:
            print("\n Da li ste mislili na:")
            for i, (broj, skor) in enumerate(sugestije[:5], 1):
                print(f"  {i}. {get_kontakt_info(broj)}")
            return
    # Unos pozvanog
    callee = autocomplete_input("Unesite broj pozvanog: ", tip='broj')
    callee_norm = normalizuj_broj(callee)

    if not validan_broj(callee_norm):
        print("Neispravan broj pozvanog!")
        return

    if callee_norm in blokirani_brojevi:
        print(f"Broj {callee} je blokiran i ne može biti pozvan!")
        return

    if callee_norm not in kontakti:
        print(f"\n Broj {caller_norm} ne postoji u imeniku.")

        sugestije = did_you_mean(callee_norm)
        if sugestije:
            print("\n Da li ste mislili na:")
            for i, (broj, skor) in enumerate(sugestije[:5], 1):
                print(f"  {i}. {get_kontakt_info(broj)}")
            return

    if caller_norm == callee_norm:
        print("Pozivalac i pozvani ne mogu biti isti")
        return

    print(f"\n{get_kontakt_info(caller_norm)} zove {get_kontakt_info(callee_norm)}...")
    print("Pritisnite Enter da prekinete poziv...\n")

    start_time = time.time()
    pocetak = datetime.now()

    # Thread za non-blocking input
    input_received = threading.Event()

    def wait_for_input():
        input()
        input_received.set()

    input_thread = threading.Thread(target=wait_for_input, daemon=True)
    input_thread.start()

    while not input_received.is_set():
        elapsed = time.time() - start_time
        print(f"\rTrajanje: {formatiraj_trajanje(elapsed)}", end='', flush=True)
        time.sleep(1)

    # Poziv prekinut
    trajanje_sek = int(time.time() - start_time)

    print("\n\nPoziv zavrsen")

    print("Informacije")
    print(f"\nPozivalac:    {get_kontakt_info(caller_norm)}")
    print(f"Pozvani:      {get_kontakt_info(callee_norm)}")
    print(f"Datum/vreme:  {pocetak.strftime('%d.%m.%Y %H:%M:%S')}")
    print(f"Trajanje:     {formatiraj_trajanje(trajanje_sek)}")
    print("--------------------------------------------------------")

    graph.add_call(caller_norm, callee_norm, trajanje_sek, pocetak)
    print("Poziv dodat u graf.")



def simulacija_pozivanja_iz_fajla():
    print("\n================================")
    print("Simulacija pozivanja iz fajla")
    print("================================")


    fajl = "simulacija.txt"


    pozivi = []
    ukupno_trajanje = 0
    neispravnih = 0
    blokiranih = 0
    uspesno = 0

    print(f"\nUčitavanje poziva...")
    with open(fajl, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):

            line = line.strip()
            if not line:
                continue

            parts = [p.strip() for p in line.split(',')]
            if len(parts) >= 4:
                caller = parts[0]
                callee = parts[1]
                datum_vreme = parts[2]
                trajanje = parts[3]

                caller_norm = normalizuj_broj(caller)
                callee_norm = normalizuj_broj(callee)

                if not validan_broj(caller_norm) or not validan_broj(callee_norm):
                    neispravnih += 1
                    continue

                if caller_norm in blokirani_brojevi or callee_norm in blokirani_brojevi:
                    blokiranih += 1
                    continue

                trajanje_sek = parsiraj_trajanje(trajanje)

                try:
                    vreme = datetime.strptime(datum_vreme, '%d.%m.%Y %H:%M:%S')
                except:
                    vreme = datetime.now()

                graph.add_call(caller_norm, callee_norm, trajanje_sek, vreme)
                uspesno += 1

                pozivi.append({
                    'caller': caller,
                    'callee': callee,
                    'datum_vreme': datum_vreme,
                    'trajanje': trajanje_sek
                })
                ukupno_trajanje += trajanje_sek

    print("\n======================")
    print("Sumarni podaci")
    print("======================")
    print(f"Ukupno poziva u fajlu: {len(pozivi) + blokiranih + neispravnih} ")
    print(f"Uspesno dodatih: {uspesno} ")
    print(f"Ukupno blokiranih: {blokiranih} ")
    print(f"Nesispravnih brojeva: {neispravnih} ")
    print(f"Ukupno trajanje:  {formatiraj_trajanje(ukupno_trajanje)}")
    if len(pozivi) > 0:
        prosecno = ukupno_trajanje / len(pozivi)
        print(f"Prosečno trajanje: {formatiraj_trajanje(prosecno)}")

    print("------------------------")
    for i, poziv in enumerate(pozivi, 1):
        caller_info = get_kontakt_info(normalizuj_broj(poziv['caller']))
        callee_info = get_kontakt_info(normalizuj_broj(poziv['callee']))
        print(f"{i:2}. {caller_info} -> {callee_info}")
        print(f"    {poziv['datum_vreme']} | {formatiraj_trajanje(poziv['trajanje'])}")


def istorija_poziva_dva_broja():
    print("\n==============================")
    print("ISTORIJA POZIVA ZA DVA BROJA")
    print("==============================")
    print("Dodajte * za autocomplete (npr: 064*)")

    broj1 = autocomplete_input("\nUnesite prvi broj: ", tip='broj')
    broj1_norm = normalizuj_broj(broj1)

    if broj1_norm not in kontakti and broj1_norm not in graph.nodes:
        print(f"\nBroj {broj1} ne postoji u sistemu")

        sugestije = did_you_mean(broj1_norm)
        if sugestije:
            print("\nDa li ste mislili na:")
            for i, (broj, skor) in enumerate(sugestije[:5], 1):
                print(f"  {i}. {get_kontakt_info(broj)}")
        return

    broj2 = autocomplete_input("Unesite drugi broj: ", tip='broj')
    broj2_norm = normalizuj_broj(broj2)

    if broj2_norm not in kontakti and broj2_norm not in graph.nodes:
        print(f"\nBroj {broj2} ne postoji u sistemu")

        sugestije = did_you_mean(broj2_norm)
        if sugestije:
            print("\nDa li ste mislili na:")
            for i, (broj, skor) in enumerate(sugestije[:5], 1):
                print(f"  {i}. {get_kontakt_info(broj)}")
        return

    pozivi = graph.istorija_poziva(broj1_norm, broj2_norm)

    if not pozivi:
        print("\n Nema istorije poziva izmedju ova dva broja.")
        return

    print(f"\n=======================================================================")
    print(f"ISTORIJA: {get_kontakt_info(broj1_norm)} i {get_kontakt_info(broj2_norm)}")
    print("========================================================================")
    print(f"Pronadjeno {len(pozivi)} poziva:\n")

    for i, poziv in enumerate(pozivi, 1):
        vreme = poziv.vremePoziva.strftime('%d.%m.%Y %H:%M:%S')
        trajanje = formatiraj_trajanje(poziv.trajanjePoziva)

        if poziv.izvor == broj1_norm:
            smer = f"{get_kontakt_info(broj1_norm)} -> {get_kontakt_info(broj2_norm)}"
        else:
            smer = f"{get_kontakt_info(broj2_norm)} -> {get_kontakt_info(broj1_norm)}"

        print(f"{i:3}. {vreme} | {trajanje:8} | {smer}")



def istorija_poziva_jedan_broj():
    print("\n=============================")
    print("Istorija poziva za jedan broj")
    print("=============================")
    print("Dodajte * za autocomplete (npr: 064*)")

    broj = autocomplete_input("\nUnesite broj: ", tip='broj')
    broj_norm = normalizuj_broj(broj)

    if broj_norm not in kontakti and broj_norm not in graph.nodes:
        print(f"\nBroj {broj} ne postoji u sistemu")

        slicni = did_you_mean(broj_norm)
        if slicni:
            print("\nDa li ste mislili na:")
            for i, (slican_broj, skor) in enumerate(slicni[:5], 1):
                print(f"  {i}. {get_kontakt_info(slican_broj)}")
        return

    pozivi = graph.istorija_poziva(broj_norm)

    if not pozivi:
        print(f"\nNema istorije poziva za broj {broj}.")
        return

    print(f"\n=====================================")
    print(f"ISTORIJA: {get_kontakt_info(broj_norm)}")
    print("==========================================")
    print(f"Pronadjeno {len(pozivi)} poziva:\n")
    print(f"{'#':>3} | {'Datum/Vreme':<20} | {'Trajanje':<10} | {'Tip':>8} | Drugi broj")
    print("-----------------------------------------------------------------------------------")

    for i, poziv in enumerate(pozivi, 1):
        vreme = poziv.vremePoziva.strftime('%d.%m.%Y %H:%M:%S')
        trajanje = formatiraj_trajanje(poziv.trajanjePoziva)

        if poziv.izvor == broj_norm:
            tip = "Odlazni"
            drugi_broj = get_kontakt_info(poziv.destinacija)
        else:
            tip = "Dolazni"
            drugi_broj = get_kontakt_info(poziv.izvor)

        print(f"{i:3} | {vreme:<20} | {trajanje:<10} | {tip:>8} | {drugi_broj}")


def pretraga_imenika():
    print("\n===============================================" )
    print("PRETRAGA TELEFONSKOG IMENIKA")
    print("===============================================")
    print("1. Pretraga po imenu")
    print("2. Pretraga po prezimenu")
    print("3. Pretraga po broju telefona")

    izbor = input("\nIzaberite opciju: ").strip()

    if izbor == '1':
        pretraga_po_imenu()
    elif izbor == '2':
        pretraga_po_prezimenu()
    elif izbor == '3':
        pretraga_po_broju()
    else:
        print("Nepoznata opcija")


def pretraga_po_imenu():
    print("\nDodajte * za autocomplete (npr: Mar*)")
    upit = autocomplete_input("Unesite ime za pretragu: ", tip='ime')
    rezultati = phonebook_trie.search_by_first_name(upit)
    prikazi_rezultate_pretrage(rezultati, upit, "ime")


def pretraga_po_prezimenu():
    print("\nDodajte * za autocomplete (npr: Mar*)")
    upit = autocomplete_input("Unesite prezime za pretragu: ", tip='prezime')
    rezultati = phonebook_trie.search_by_last_name(upit)
    prikazi_rezultate_pretrage(rezultati, upit, "prezime")


def pretraga_po_broju():
    print("\nDodajte * za autocomplete (npr: 064*)")
    upit = autocomplete_input("Unesite pocetne cifre broja: ", tip='broj')
    rezultati = phonebook_trie.search_by_phone(upit)
    prikazi_rezultate_pretrage(rezultati, upit, "broj")


def prikazi_rezultate_pretrage(rezultati, upit, tip):
    if not rezultati:
        print("\nNema rezultata pretrage.")

        if tip == "broj":
            sugestije = did_you_mean(upit)
            if sugestije:
                print("\nDa li ste mislili na:")
                for i, (broj, skor) in enumerate(sugestije[:5], 1):
                    print(f"  {i}. {get_kontakt_info(broj)}")
        return

    rangirani = []
    for ime_ili_broj, kontakt_data in rezultati:
        broj = kontakt_data['phone']
        broj_norm = normalizuj_broj(broj)
        popularnost = graph.izracunaj_popularnost(broj_norm)
        rangirani.append((broj_norm, kontakt_data, popularnost))

    rangirani.sort(key=lambda x: x[2], reverse=True)

    print(f"\n==================================================================")
    print(f"REZULTATI PRETRAGE: '{upit}'")
    print("===================================================================")
    print(f"Pronadeno {len(rangirani)} rezultata (rangirano po popularnosti):\n")
    print(f"{'#':>3} | {'Ime i Prezime':<25} | {'Broj':<18} | Popularnost")
    print("-------------------------------------------------------------------")

    for i, (broj, kontakt, popularnost) in enumerate(rangirani[:20], 1):
        ime = kontakt.get('first_name', '')
        prezime = kontakt.get('last_name', '')
        puno_ime = f"{ime} {prezime}".strip()

        if tip == 'ime' and upit.lower() in ime.lower():
            idx = ime.lower().index(upit.lower())
            ime_display = ime[:idx] + "*" + ime[idx:idx + len(upit)] + "*" + ime[idx + len(upit):]
            puno_ime = f"{ime_display} {prezime}"
        elif tip == 'prezime' and upit.lower() in prezime.lower():
            idx = prezime.lower().index(upit.lower())
            prezime_display = prezime[:idx] + "*" + prezime[idx:idx + len(upit)] + "*" + prezime[idx + len(upit):]
            puno_ime = f"{ime} {prezime_display}"

        print(f"{i:3} | {puno_ime:<25} | {kontakt['phone']:<18} | {popularnost:>6.2f}")


def did_you_mean(upit):
    svi_brojevi = list(kontakti.keys())
    slicnosti = []

    for broj in svi_brojevi:
        skor = SequenceMatcher(None, upit, broj).ratio()
        if skor > 0.5:  # Threshold
            slicnosti.append((broj, skor))

    slicnosti.sort(key=lambda x: x[1], reverse=True)
    return slicnosti[:5]


# ===== Simulacija opterecenja =====

def simulacija_opterecenja():
    print("\n" + "=" * 80)
    print("SIMULACIJA OPTEREĆENJA TELEFONSKE CENTRALE")
    print("=" * 80)
    print("Generisanje 1000 poziva u toku 1 minuta...")
    print("Pritisnite 'p' za pauzu, 'n' za nastavak, 'q' za prekid\n")

    start_time = time.time()
    ciljno_vreme = 60  # sekunde
    broj_poziva = 1000
    interval = ciljno_vreme / broj_poziva

    generisani_pozivi = 0
    blokirano = 0
    ukupno_trajanje = 0

    paused = False
    finished = False

    # Non-blocking input thread
    command = [None]

    def input_thread():
        while not finished:
            try:
                cmd = input().strip().lower()
                command[0] = cmd
            except:
                pass

    t = threading.Thread(target=input_thread, daemon=True)
    t.start()

    try:
        while generisani_pozivi < broj_poziva:
            if command[0] == 'p':
                paused = True
                print("\n [PAUZIRANO] Pritisnite 'n' za nastavak...")
                command[0] = None
            elif command[0] == 'n':
                paused = False
                print(" [NASTAVLJENO]")
                command[0] = None
            elif command[0] == 'q':
                print("\n [PREKINUTO]")
                break

            if paused:
                time.sleep(0.1)
                continue

            # Generiši slučajan poziv
            svi_brojevi = list(kontakti.keys())
            if len(svi_brojevi) < 2:
                print("Nedovoljno brojeva u bazi!")
                break

            caller = random.choice(svi_brojevi)
            callee = random.choice(svi_brojevi)
            while caller == callee:
                callee = random.choice(svi_brojevi)

            # Proveri blokirane brojeve
            if caller in blokirani_brojevi or callee in blokirani_brojevi:
                blokirano += 1
            else:
                # Generiši trajanje (10-600 sekundi)
                trajanje = random.randint(10, 600)
                ukupno_trajanje += trajanje

                # Dodaj poziv u graf
                graph.add_call(caller, callee, trajanje)

            generisani_pozivi += 1

            if generisani_pozivi % 100 == 0:
                proteklo = time.time() - start_time
                print(f"Generisano: {generisani_pozivi}/{broj_poziva} | "
                      f"Proteklo: {int(proteklo)}s | Blokirano: {blokirano}")

            time.sleep(interval)

        finished = True


        print("\n=======================================================" )
        print("Izvestaj simulacije")
        print("=======================================================")
        print(f"Ukupno generisano poziva: {generisani_pozivi}")
        print(f"Blokirano poziva:         {blokirano}")
        print(f"Uspesno procesuirano:     {generisani_pozivi - blokirano}")

        if generisani_pozivi - blokirano > 0:
            prosecno = ukupno_trajanje / (generisani_pozivi - blokirano)
            print(f"Prosecno trajanje poziva: {formatiraj_trajanje(prosecno)}")

        print("\nTop 5 najpopularnijih brojeva:")
        print("-------------------------------------------------------------")
        top_brojevi = graph.top_pop_brojevi(5)
        for i, (broj, popularnost) in enumerate(top_brojevi, 1):
            print(f"{i}. {get_kontakt_info(broj):<50} | Popularnost: {popularnost:>8.2f}")
        print("=============================================================")

    except KeyboardInterrupt:
        print("\n\n Simulacija prekinuta")


def inicijalizuj_sistem():

    if os.path.exists('centrala_data.pkl'):
        print("\nPronadjen fajl sa sacuvanim podacima.")

        if ucitaj_pickle():
            print("\nSistem spreman za rad!")
            return

    print("\nUcitavanje podataka iz fajlova...")
    print("--------------------------------------------" )

    ucitaj_kontakte('phones.txt')
    ucitaj_blokirane('blocked.txt')

    if os.path.exists('calls.txt'):
        print("\nPronadjen fajl sa pozivima (calls.txt)")
        ucitaj_pozive('calls.txt')
    else:
        print("\ncalls.txt ne postoji! Pokrenite generate_calls.py za generisanje.")

def main():
    inicijalizuj_sistem()
    while True:
        print("====== TELEFONSKA CENTRALA ============")
        print("1. Simulacija pozivanja uživo")
        print("2. Simulacija pozivanja iz fajla")
        print("3. Istorija poziva za dva broja")
        print("4. Istorija poziva jednog broja")
        print("5. Pretraga telefonskog imenika")
        print("6. Simulacija opterećenja centrale")
        print("0. Izlaz")


        izbor = input("\nIzaberite opciju: ").strip()

        if izbor == '1':
            simulacija_pozivanja_uzivo()
        elif izbor == '2':
            simulacija_pozivanja_iz_fajla()
        elif izbor == '3':
            istorija_poziva_dva_broja()
        elif izbor == '4':
            istorija_poziva_jedan_broj()
        elif izbor == '5':
            pretraga_imenika()
        elif izbor == '6':
            simulacija_opterecenja()
        elif izbor == '0':
            print("\nDovidjenja")
            break
        else:
            print("Nepoznata opcija. Pokušajte ponovo.")




    print("\nČuvanje podataka...")
    sacuvaj_pickle()
    print("\nPodaci sacuvani. Dovidjenja")




if __name__ == '__main__':
    main()