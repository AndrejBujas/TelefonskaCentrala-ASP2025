from datetime import datetime

class Node:
    def __init__(self, broj):
        self.broj = broj
        self.dolazeci = []
        self.odlazeci = []

        self.trajanje_dolazecih = 0
        self.trajanje_odlazecih = 0

        self.popularnost = None
        self.popularnost_last_updated = None


    def dodaj_dolazeci(self, poziv):
        self.dolazeci.append(poziv)
        self.trajanje_dolazecih += poziv.trajanjePoziva
        self.popularnost = None

    def dodaj_odlazeci(self, poziv):
        self.odlazeci.append(poziv)
        self.trajanje_odlazecih += poziv.trajanjePoziva

    def get_broj(self):
        return self.broj

    def get_broj_dolazecih(self):
        return len(self.dolazeci)

    def get_broj_odlazecih(self):
        return len(self.odlazeci)

    def get_broj_ukupno(self):
        return self.get_broj_dolazecih() + self.get_broj_odlazecih()

    def get_average_call_duration(self, call_type='dolazeci'):

        if call_type == 'dolazeci':
            count = len(self.dolazeci)
            duration = self.trajanje_dolazecih
        elif call_type == 'odlazeci':
            count = len(self.odlazeci)
            duration = self.trajanje_odlazecih
        else:  # 'all'
            count = len(self.dolazeci) + len(self.odlazeci)
            duration = self.trajanje_dolazecih + self.trajanje_odlazecih

        return duration / count if count > 0 else 0


class Edge:
    def __init__(self, izvor, destinacija, trajanjePoziva, vremePoziva):
        self.izvor = izvor
        self.destinacija = destinacija
        self.trajanjePoziva = trajanjePoziva
        self.vremePoziva = vremePoziva


class Graph:

    def __init__(self):
        self.nodes = {}
        self.pop_cache = {}

    def add_phone(self, broj):
        if broj not in self.nodes:
            self.nodes[broj] = Node(broj)
        return self.nodes[broj]

    def add_call(self, caller, callee, trajanje, timestamp=None):

        caller = self._normal_broj(caller)
        callee = self._normal_broj(callee)

        if not caller or not callee or caller == callee:
            return None

        if timestamp is None:
            timestamp = datetime.now()

        caller_node = self.add_phone(caller)
        callee_node = self.add_phone(callee)

        call_edge = Edge(caller, callee, trajanje, timestamp)

        caller_node.dodaj_odlazeci(call_edge)
        callee_node.dodaj_dolazeci(call_edge)

        self.pop_cache = {}

        return call_edge

    def _normal_broj(self, broj):
        if isinstance(broj, str):
            return broj.replace(" ", "").replace("-", "")
        return broj

    def get_node(self, broj):
        broj = self._normal_broj(broj)
        return self.nodes.get(broj)

    def izracunaj_popularnost(self, broj):

        broj = self._normal_broj(broj)

        if broj in self.pop_cache:
            return self.pop_cache[broj]

        node = self.get_node(broj)
        if not node:
            return 0.0

        dolazeci_broj = node.get_broj_dolazecih() #br dolazecih poziva

        if dolazeci_broj == 0:
            self.pop_cache[broj] = 0.0
            return 0.0

        skor_poziva = dolazeci_broj * 10

        ukupno_trajanje_min = node.trajanje_dolazecih / 60.0
        skor_trajanja = ukupno_trajanje_min * 0.5

        direktni_skor = skor_poziva + skor_trajanja


        suma_pozivalaca = 0

        for call in node.dolazeci:
            caller_node = self.get_node(call.izvor)
            if caller_node:
                caller_pozivi = caller_node.get_broj_dolazecih()
                suma_pozivalaca += caller_pozivi #broj poziva pozivalaca

        if dolazeci_broj > 0:
            prosecna_pop_pozivalaca = suma_pozivalaca / dolazeci_broj
            bonus_pozivalaci = prosecna_pop_pozivalaca * 2
        else:
            bonus_pozivalaci = 0

        final_score = direktni_skor + bonus_pozivalaci

        self.pop_cache[broj] = final_score
        return final_score

    def top_pop_brojevi(self, n):
        popularnosti = []

        for broj in self.nodes.keys():
            score = self.izracunaj_popularnost(broj)
            popularnosti.append((broj, score))

        popularnosti.sort(key=lambda x: x[1], reverse=True)

        return popularnosti[:n]

    def istorija_poziva(self, broj1, broj2=None):
        broj1 = self._normal_broj(broj1)
        node1 = self.get_node(broj1)

        if not node1:
            return []

        if broj2:

            broj2 = self._normal_broj(broj2)
            calls = []


            for call in node1.odlazeci:
                if call.destinacija == broj2:
                    calls.append(call)

            # Pozivi od phone2 ka phone1
            for call in node1.dolazeci:
                if call.izvor == broj2:
                    calls.append(call)
        else:
            calls = node1.dolazeci + node1.odlazeci

        calls.sort(key=lambda x: x.vremePoziva)

        return calls

    def __len__(self):
        return len(self.nodes)