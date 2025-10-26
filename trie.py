class TrieNode:

    def __init__(self):
        self.children = {}
        self.is_end_of_word = False
        self.data = []

    def __repr__(self):
        return f"TrieNode(children={len(self.children)}, is_end={self.is_end_of_word}, data_count={len(self.data)})"


class Trie:

    def __init__(self, name="Trie"):
        self.root = TrieNode()
        self.name = name

    def _normalize_key(self, key):

        if isinstance(key, str):
            key = key.replace(" ", "").replace("-", "")
            if not key.isdigit():
                key = key.lower()
        return key

    def insert(self, key, data=None):
        key = self._normalize_key(key)

        if not key:
            return

        node = self.root


        for char in key:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]

        node.is_end_of_word = True

        if data is not None:
            if data not in node.data:
                node.data.append(data)

    def search(self, key):

        key = self._normalize_key(key)

        node = self.root

        for char in key:
            if char not in node.children:
                return None
            node = node.children[char]

        if node.is_end_of_word:
            return node.data
        return None

    def starts_with(self, prefix, max_results=None):

        prefix = self._normalize_key(prefix)

        node = self.root

        for char in prefix:
            if char not in node.children:
                return []
            node = node.children[char]

        results = []
        self._collect_all_words(node, prefix, results)

        if max_results:
            results = results[:max_results]

        return results

    def _collect_all_words(self, node, current_word, results):

        if node.is_end_of_word:
            for data in node.data: #zato sto jedno ime moze imati vise brojeva tj vise data
                results.append((current_word, data))

        for char, child_node in node.children.items():
            self._collect_all_words(child_node, current_word + char, results)

    def autocomplete(self, prefix, max=5):

        return self.starts_with(prefix, max_results=max)


    def get_all_entries(self):

        results = []
        self._collect_all_words(self.root, "", results)
        return results

    def size(self):
        return len([x for x in self.get_all_entries()])

    def __len__(self):
        return self.size()

    def __repr__(self):
        return f"Trie(name='{self.name}', size={self.size()})"


class PhoneBookTrie:

    def __init__(self):
        self.phone_trie = Trie("Phone Numbers")
        self.first_name_trie = Trie("First Names")
        self.last_name_trie = Trie("Last Names")

    def add_contact(self, phone_number, first_name=None, last_name=None):

        contact_data = {
            'phone': phone_number,
            'first_name': first_name,
            'last_name': last_name
        }

        self.phone_trie.insert(phone_number, contact_data)

        if first_name:
            self.first_name_trie.insert(first_name, contact_data)

        if last_name:
            self.last_name_trie.insert(last_name, contact_data)

    def search_by_phone(self, phone_prefix):
        return self.phone_trie.starts_with(phone_prefix)

    def search_by_first_name(self, name_prefix):
        return self.first_name_trie.starts_with(name_prefix)

    def search_by_last_name(self, name_prefix):
        return self.last_name_trie.starts_with(name_prefix)

    def search_all(self, query):

        return {
            'phones': self.search_by_phone(query),
            'first_names': self.search_by_first_name(query),
            'last_names': self.search_by_last_name(query)
        }

    def autocomplete_phone(self, prefix, max_suggestions=5):
        return self.phone_trie.autocomplete(prefix, max_suggestions)

    def autocomplete_first_name(self, prefix, max_suggestions=5):
        return self.first_name_trie.autocomplete(prefix, max_suggestions)

    def autocomplete_last_name(self, prefix, max_suggestions=5):
        return self.last_name_trie.autocomplete(prefix, max_suggestions)

    def __repr__(self):
        return (f"PhoneBookTrie(\n"
                f"  phones: {len(self.phone_trie)},\n"
                f"  first_names: {len(self.first_name_trie)},\n"
                f"  last_names: {len(self.last_name_trie)}\n"
                f")")