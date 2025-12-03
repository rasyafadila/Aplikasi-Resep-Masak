import customtkinter as ctk
import os
from PIL import Image, ImageTk
# Import controller yang sudah kita buat
from .controller_json import ResepController

# --- KONFIGURASI DAN DATA ---
ctk.set_appearance_mode("System")  # Pilihan: "System", "Dark", "Light"
ctk.set_default_color_theme("blue")

# Tambahkan import CTkMessagebox untuk konfirmasi dialog
try:
    from CTkMessagebox import CTkMessagebox
except ImportError:
    print("Peringatan: CTkMessagebox tidak terinstal. Silakan jalankan: pip install CTkMessagebox")
    # Definisikan kelas fallback agar program tetap bisa berjalan
    class CTkMessagebox:
        def __init__(self, title=None, message=None, icon=None, **kwargs):
            print(f"{title}: {message}")
        
        def show(self):
            pass
        
        @staticmethod
        def show_message(title, message, icon):
            print(f"{title}: {message}")
        
        @staticmethod
        def ask_question(title, message, icon):
            # Di fallback, asumsikan selalu "yes" untuk testing
            print(f"{title}: {message} (Fallback: Yes)")
            return True


# --- KELAS UTAMA APLIKASI ---
class ResepApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Inisialisasi Controller
        self.controller = ResepController()
        
        # Konfigurasi Jendela
        self.title("🍲 Aplikasi Resep Masakan")
        self.geometry("1000x700")
        
        # Grid Utama (1: Navigasi, 2: Konten)
        self.grid_columnconfigure(0, weight=0)  # Sidebar
        self.grid_columnconfigure(1, weight=1)  # Konten
        self.grid_rowconfigure(0, weight=1)
        
        self.current_frame = None  # Untuk melacak frame yang sedang ditampilkan
        # Panggil Setup UI
        self._setup_sidebar()
        
        # Tampilkan Halaman Awal
        self.show_frame("daftar")

    def _setup_sidebar(self):
        """Membuat sidebar navigasi yang statis."""
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(4, weight=1)
        ctk.CTkLabel(self.sidebar_frame, text="CookEasy", 
                     font=ctk.CTkFont(size=22, weight="bold")).grid(row=0, column=0, padx=20, pady=(20, 10))
        
        # Tombol Navigasi 
        ctk.CTkButton(self.sidebar_frame, text="📚 Daftar Resep", 
                      command=lambda: self.show_frame("daftar")).grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        
        ctk.CTkButton(self.sidebar_frame, text="⭐ Favorit", 
                      command=lambda: self.show_frame("favorit")).grid(row=3, column=0, padx=20, pady=10, sticky="ew")
        
        ctk.CTkButton(self.sidebar_frame, text="➕ Tambah Resep", 
                      command=lambda: self.show_frame("tambah")).grid(row=4, column=0, padx=20, pady=10, sticky="ew")
        
        # Dropdown untuk Mode Tampilan 
        appearance_label = ctk.CTkLabel(self.sidebar_frame, text="Mode Tampilan:", anchor="w")
        appearance_label.grid(row=5, column=0, padx=20, pady=(10, 0), sticky="s")
        self.appearance_mode_optionemenu = ctk.CTkOptionMenu(self.sidebar_frame, values=["Light", "Dark", "System"], 
                                                             command=ctk.set_appearance_mode)
        self.appearance_mode_optionemenu.grid(row=6, column=0, padx=20, pady=(0, 20), sticky="s")
        self.appearance_mode_optionemenu.set("System")
    
    def show_frame(self, name, resep_id=None):
        """Menghapus frame lama dan menampilkan frame baru."""
        # Refresh data dari controller sebelum menampilkan frame
        self.controller.resep_data = self.controller._muat_resep()

        if self.current_frame:
            self.current_frame.destroy()
            
        resep_data = self.controller.get_all_resep()

        if name == "daftar":
            self.current_frame = DaftarResepFrame(self)
        elif name == "favorit":
            self.current_frame = FavoritFrame(self)
        elif name == "tambah":
            self.current_frame = FormTambahResepFrame(self)
        elif name == "detail" and resep_id is not None:
            resep = self.controller.get_resep_by_id(resep_id)
            if resep:
                self.current_frame = DetailResepFrame(self, resep)
            else:
                self.current_frame = ctk.CTkLabel(self, text="Resep tidak ditemukan.")
                self.current_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
                return

        self.current_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

# --- KELAS FRAME KONTEN ---

class DaftarResepFrame(ctk.CTkScrollableFrame):
    def __init__(self, master):
        super().__init__(master, label_text="Daftar Semua Resep", label_font=ctk.CTkFont(size=20, weight="bold"))
        self.master = master
        self.grid_columnconfigure(0, weight=1)
        self.search_var = ctk.StringVar()
        self._setup_search()
        self.list_container = ctk.CTkFrame(self)  # Container khusus untuk daftar resep
        self.list_container.pack(fill="both", expand=True, padx=10, pady=5)
        self.tampilkan_list_resep()

    def _setup_search(self):
        """Menambahkan search bar di atas list resep."""
        self.search_container = ctk.CTkFrame(self)
        self.search_container.pack(fill="x", padx=10, pady=(10, 5))
        self.search_container.grid_columnconfigure(0, weight=1)
        self.search_container.grid_columnconfigure(1, weight=3)  # Entry lebih lebar
        
        ctk.CTkLabel(self.search_container, text="🔍 Cari Resep:", anchor="w").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.search_entry = ctk.CTkEntry(self.search_container, textvariable=self.search_var, placeholder_text="Ketik nama resep...")
        self.search_entry.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        self.search_entry.bind("<KeyRelease>", self._on_search_change)  # Bind untuk memicu filter saat mengetik
        
    def _on_search_change(self, event=None):
        """Memfilter resep berdasarkan input search."""
        query = self.search_var.get().lower()
        
        # Hanya hancurkan anak-anak dari list_container (bukan seluruh frame)
        for widget in self.list_container.winfo_children():
            widget.destroy()
        
        self.tampilkan_list_resep(filtered=True, query=query)
        
    def tampilkan_list_resep(self, filtered=False, query=""):
        """Membuat kartu-kartu resep di dalam list_container."""
        resep_list = self.master.controller.get_all_resep()

        if filtered and query:
            filtered_list = []
            for r in resep_list:
                is_in_name = query in r.get('nama', '').lower()
                bahan_str = ' '.join(r.get('bahan', [])).lower()
                is_in_bahan = query in bahan_str
                if is_in_name or is_in_bahan:
                    filtered_list.append(r)
            resep_list = filtered_list 
            
        if not resep_list:
            ctk.CTkLabel(self.list_container, text="Tidak ada resep yang cocok.").pack(pady=20)
            return
            
        for i, resep in enumerate(resep_list):
            card = ctk.CTkFrame(self.list_container, fg_color=("gray80", "gray20"))
            card.pack(fill="x", pady=5)
            card.grid_columnconfigure(0, weight=1)
            
            # Judul Resep
            ctk.CTkLabel(card, text=resep['nama'], font=ctk.CTkFont(size=18, weight="bold"), anchor="w").grid(row=0, column=0, padx=15, pady=10, sticky="w")
            
            # Tombol Favorit (Bintang)
            favorit_text = "⭐" if resep['favorit'] else "☆"
            favorit_btn = ctk.CTkButton(card, text=favorit_text, width=40, 
                                        command=lambda r_id=resep['id']: self.toggle_favorit(r_id))
            favorit_btn.grid(row=0, column=1, padx=10, pady=10, sticky="e")
            
            # Tombol Lihat Detail
            ctk.CTkButton(card, text="Lihat Detail", 
                          command=lambda r_id=resep['id']: self.master.show_frame("detail", r_id)).grid(row=0, column=2, padx=10, pady=10, sticky="e")
            
            # Tombol Hapus
            ctk.CTkButton(
                card, 
                text="Trash", width=40, fg_color="red", hover_color="darkred",
                command=lambda rid=resep['id'], rname=resep['nama']: self.konfirmasi_hapus(rid, rname)
            ).grid(row=0, column=3, padx=(0, 10), pady=10, sticky="e")

    def toggle_favorit(self, resep_id):
        """Toggle status favorit resep melalui controller."""
        self.master.controller.toggle_favorit(resep_id)
        # Refresh data dari controller setelah toggle
        self.master.controller.resep_data = self.master.controller._muat_resep()
        self._on_search_change()  # Refresh tampilan
        
    def konfirmasi_hapus(self, resep_id, resep_nama):
        """Menampilkan dialog konfirmasi sebelum menghapus."""
        if CTkMessagebox.ask_question("Konfirmasi Hapus", f"Yakin ingin menghapus resep '{resep_nama}'?", icon="warning"):
            self.master.controller.hapus_resep(resep_id)
            self.master.controller.resep_data = self.master.controller._muat_resep()
            self._on_search_change()  

class FavoritFrame(ctk.CTkScrollableFrame):
    def __init__(self, master):
        super().__init__(master, label_text="Resep Favorit", label_font=ctk.CTkFont(size=20, weight="bold"))
        self.master = master
        self.grid_columnconfigure(0, weight=1)
        self.tampilkan_favorit()

    def tampilkan_favorit(self):
        """Menampilkan resep favorit dengan gambar jika ada."""
        favorit_list = [r for r in self.master.controller.get_all_resep() if r['favorit']]
        
        if not favorit_list:
            ctk.CTkLabel(self, text="Belum ada resep favorit. Tambahkan favorit dari daftar resep!", 
                         font=ctk.CTkFont(size=16)).pack(pady=50)
            return
            
        for resep in favorit_list:
            card = ctk.CTkFrame(self, fg_color=("gray80", "gray20"))
            card.pack(fill="x", padx=10, pady=5)
            card.grid_columnconfigure(1, weight=1)
            
            # Gambar jika ada
            img_loaded = False
            if resep['gambar'] and os.path.exists(resep['gambar']):
                try:
                    img = Image.open(resep['gambar'])
                    img = img.resize((100, 100), Image.Resampling.LANCZOS)
                    ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(100, 100))
                    img_label = ctk.CTkLabel(card, image=ctk_img, text="")
                    img_label.grid(row=0, column=0, rowspan=2, padx=10, pady=10)
                    img_label.image = ctk_img  # Menyimpan referensi agar gambar tidak hilang
                    img_loaded = True
                except Exception as e:
                    print(f"Error loading image: {e}")
            
            if not img_loaded:
                ctk.CTkLabel(card, text="[No Image]", width=100, height=100, fg_color="gray50").grid(row=0, column=0, rowspan=2, padx=10, pady=10)

            # Judul Resep
            ctk.CTkLabel(card, text=resep['nama'], font=ctk.CTkFont(size=18, weight="bold"), anchor="w").grid(row=0, column=1, padx=15, pady=10, sticky="w")
            
            # Tombol Lihat Detail
            ctk.CTkButton(card, text="Lihat Detail", 
                          command=lambda r_id=resep['id']: self.master.show_frame("detail", r_id)).grid(row=1, column=1, padx=10, pady=10, sticky="e")

class DetailResepFrame(ctk.CTkScrollableFrame):
    def __init__(self, master, resep):
        super().__init__(master, label_text=f"Detail Resep: {resep['nama']}", label_font=ctk.CTkFont(size=20, weight="bold"))
        self.master = master
        self.resep = resep
        self.grid_columnconfigure(0, weight=1)
        self.display_details()

    def display_details(self):
        """Menampilkan bahan dan langkah memasak, dengan gambar jika ada."""
        
        # Gambar jika ada
        if self.resep['gambar'] and os.path.exists(self.resep['gambar']):
            try:
                img = Image.open(self.resep['gambar'])
                img = img.resize((300, 200), Image.Resampling.LANCZOS)
                ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(300, 200))
                img_label = ctk.CTkLabel(self, image=ctk_img, text="")
                img_label.pack(pady=(10, 20))
                img_label.image = ctk_img
            except Exception as e:
                print(f"Error loading image: {e}")
                ctk.CTkLabel(self, text="[Gagal Memuat Gambar]").pack(pady=(10, 20))
        else:
            ctk.CTkLabel(self, text="[Tidak Ada Gambar]").pack(pady=(10, 20))

        # Judul Besar
        ctk.CTkLabel(self, text=self.resep['nama'], font=ctk.CTkFont(size=36, weight="bold")).pack(pady=(10, 20))
        
        # --- Bagian Bahan ---
        bahan_frame = ctk.CTkFrame(self, fg_color=("gray90", "gray10"))
        bahan_frame.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(bahan_frame, text="✅ Bahan-Bahan", font=ctk.CTkFont(size=20, weight="bold"), anchor="w").pack(fill="x", padx=15, pady=(10, 5))
        
        # Pastikan bahan adalah list
        bahan_list = self.resep.get('bahan', [])
        bahan_text = "\n".join([f"• {b}" for b in bahan_list])
        ctk.CTkLabel(bahan_frame, text=bahan_text, justify="left", anchor="w").pack(fill="x", padx=25, pady=(0, 10))
        
        # --- Bagian Langkah ---
        langkah_frame = ctk.CTkFrame(self, fg_color=("gray90", "gray10"))
        langkah_frame.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(langkah_frame, text="📝 Langkah Memasak", font=ctk.CTkFont(size=20, weight="bold"), anchor="w").pack(fill="x", padx=15, pady=(10, 5))
        
        # Pastikan langkah adalah list
        langkah_list = self.resep.get('langkah', [])
        langkah_text = "\n".join([f"{i+1}. {l}" for i, l in enumerate(langkah_list)])
        ctk.CTkLabel(langkah_frame, text=langkah_text, justify="left", anchor="w").pack(fill="x", padx=25, pady=(0, 10))
        
        # Tombol Kembali
        ctk.CTkButton(self, text="⬅️ Kembali ke Daftar", command=lambda: self.master.show_frame("daftar")).pack(pady=30)

class FormTambahResepFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.grid_columnconfigure(0, weight=1)
        self.create_form()
        
    def create_form(self):
        ctk.CTkLabel(self, text="➕ Tambah Resep Baru", font=ctk.CTkFont(size=28, weight="bold")).pack(pady=20)
        
        # Container untuk Kontrol
        form_scroll_frame = ctk.CTkScrollableFrame(self)
        form_scroll_frame.pack(fill="both", expand=True, padx=20, pady=10)
        form_scroll_frame.grid_columnconfigure(0, weight=1)
        
        # 1. Input Nama Resep
        ctk.CTkLabel(form_scroll_frame, text="Nama Resep:", anchor="w", font=ctk.CTkFont(size=16, weight="bold")).pack(fill="x", padx=15, pady=(10, 0))
        self.entry_nama = ctk.CTkEntry(form_scroll_frame, placeholder_text="Contoh: Ayam Bakar Madu")
        self.entry_nama.pack(fill="x", padx=15, pady=(0, 10))
        
        # 2. Input Path Gambar (Opsional)
        ctk.CTkLabel(form_scroll_frame, text="Path Gambar (Opsional, contoh: assets/nasi_goreng.jpg):", anchor="w", font=ctk.CTkFont(size=16, weight="bold")).pack(fill="x", padx=15, pady=(10, 0))
        self.entry_gambar = ctk.CTkEntry(form_scroll_frame, placeholder_text="Kosongkan jika tidak ada")
        self.entry_gambar.pack(fill="x", padx=15, pady=(0, 10))
        
        # 3. Input Bahan
        ctk.CTkLabel(form_scroll_frame, text="Bahan-Bahan (Satu bahan per baris):", anchor="w", font=ctk.CTkFont(size=16, weight="bold")).pack(fill="x", padx=15, pady=(10, 0))
        self.textbox_bahan = ctk.CTkTextbox(form_scroll_frame, height=120)
        self.textbox_bahan.pack(fill="x", padx=15, pady=(0, 10))
        
        # 4. Input Langkah Memasak
        ctk.CTkLabel(form_scroll_frame, text="Langkah Memasak (Satu langkah per baris):", anchor="w", font=ctk.CTkFont(size=16, weight="bold")).pack(fill="x", padx=15, pady=(10, 0))
        self.textbox_langkah = ctk.CTkTextbox(form_scroll_frame, height=200)
        self.textbox_langkah.pack(fill="x", padx=15, pady=(0, 20))
        
        # Tombol Simpan
        ctk.CTkButton(self, text="💾 Simpan Resep", command=self.simpan_resep_baru).pack(pady=(10, 20))

    def simpan_resep_baru(self):
        """Mengambil data dari form dan menyimpannya melalui controller."""
        nama = self.entry_nama.get().strip()
        gambar = self.entry_gambar.get().strip() or ""  # Kosongkan jika tidak diisi
    
    # Ambil bahan dan langkah
        bahan_raw = self.textbox_bahan.get("1.0", "end-1c")
        bahan = [line.strip() for line in bahan_raw.split('\n') if line.strip()]
    
        langkah_raw = self.textbox_langkah.get("1.0", "end-1c")
        langkah = [line.strip() for line in langkah_raw.split('\n') if line.strip()]

    # Validasi
        if not nama:
            CTkMessagebox(title="Error", message="Nama resep wajib diisi!", icon="cancel").show()
            return
        if not bahan:
            CTkMessagebox(title="Error", message="Bahan-bahan wajib diisi (minimal 1 bahan)!", icon="cancel").show()
            return
        if not langkah:
            CTkMessagebox(title="Error", message="Langkah memasak wajib diisi (minimal 1 langkah)!", icon="cancel").show()
            return
    # Simpan ke controller
        self.master.controller.tambah_resep(nama, bahan, langkah, gambar)

    # Tampilkan pesan sukses — PAKAI CTkMessagebox (bukan ctk.CTkMessageBox!)
        CTkMessagebox(title="Sukses!", message=f"Resep '{nama}' berhasil ditambahkan!", icon="check").show()

    # Kembali ke daftar resep
        self.master.show_frame("daftar")