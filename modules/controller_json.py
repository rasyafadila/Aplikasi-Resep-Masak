import json
import os

DATA_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "resep.json")

class ResepController:
    def __init__(self):
        self.resep_data = self._muat_resep()

    def _muat_resep(self):
        if not os.path.exists(DATA_FILE):
            return []
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for resep in data:
                    resep.setdefault('favorit', False)
                    resep.setdefault('gambar', "")
                return data
        except Exception as e:
            print(f"Error loading data: {e}")
            return []

    def _simpan(self):
        os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.resep_data, f, indent=2, ensure_ascii=False)

    def get_all_resep(self):
        return self.resep_data

    def get_resep_by_id(self, rid):
        for r in self.resep_data:
            if r['id'] == rid:
                return r
        return None

    def toggle_favorit(self, rid):
        for r in self.resep_data:
            if r['id'] == rid:
                r['favorit'] = not r['favorit']
                break
        self._simpan()

    def hapus_resep(self, rid):
        self.resep_data = [r for r in self.resep_data if r['id'] != rid]
        self._simpan()

    def tambah_resep(self, nama, bahan, langkah, gambar=""):
        new_id = max((r['id'] for r in self.resep_data), default=0) + 1
        resep_baru = {
            "id": new_id,
            "nama": nama,
            "gambar": gambar,
            "bahan": bahan,
            "langkah": langkah,
            "favorit": False
        }
        self.resep_data.append(resep_baru)
        self._simpan()