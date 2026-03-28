import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date
from service.categoria_service import CategoriaService
from service.gasto_service import GastoService
from repository.gasto_repository import GastoRepository

# ─── intentar importar tkcalendar (opcional) ───────────────────────────────
try:
    from tkcalendar import DateEntry
    CALENDAR_DISPONIBLE = True
except ImportError:
    CALENDAR_DISPONIBLE = False


class AppWindow:
    """Ventana principal de la aplicación."""

    # ───────────────────────────── INIT ──────────────────────────────────────
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Control de Gastos Personales")
        self.root.geometry("1050x680")
        self.root.configure(bg="#1e1e2e")
        self.root.minsize(900, 600)

        self.cat_service = CategoriaService()
        self.gas_service = GastoService()
        self.gas_repo    = GastoRepository()

        # ID en edición (None = modo crear)
        self._edit_gasto_id    = None
        self._edit_cat_id      = None

        self._build_styles()
        self._build_ui()
        self._cargar_datos()

    # ─────────────────────────── ESTILOS ─────────────────────────────────────
    def _build_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        BG, FG     = "#1e1e2e", "#cdd6f4"
        SURFACE    = "#313244"
        ACCENT     = "#cba6f7"
        ACCENT2    = "#89b4fa"
        ENTRY_BG   = "#45475a"
        HEADER_BG  = "#181825"

        style.configure("TFrame",        background=BG)
        style.configure("TLabel",        background=BG,      foreground=FG,    font=("Segoe UI", 10))
        style.configure("Header.TLabel", background=BG,      foreground=ACCENT, font=("Segoe UI", 14, "bold"))
        style.configure("Sub.TLabel",    background=SURFACE, foreground=FG,    font=("Segoe UI", 9))
        style.configure("TEntry",        fieldbackground=ENTRY_BG, foreground=FG, insertcolor=FG, font=("Segoe UI", 10))
        style.configure("TCombobox",     fieldbackground=ENTRY_BG, foreground=FG, font=("Segoe UI", 10))
        style.map("TCombobox", fieldbackground=[("readonly", ENTRY_BG)])

        style.configure("TNotebook",           background=BG,      tabmargins=[0,0,0,0])
        style.configure("TNotebook.Tab",       background=SURFACE, foreground=FG,
                        font=("Segoe UI", 10, "bold"), padding=[16, 8])
        style.map("TNotebook.Tab",
                  background=[("selected", ACCENT)],
                  foreground=[("selected", "#1e1e2e")])

        style.configure("Treeview",            background=SURFACE, foreground=FG,
                        fieldbackground=SURFACE, rowheight=28, font=("Segoe UI", 9))
        style.configure("Treeview.Heading",    background=HEADER_BG, foreground=ACCENT2,
                        font=("Segoe UI", 9, "bold"))
        style.map("Treeview", background=[("selected", ACCENT)], foreground=[("selected", "#1e1e2e")])

        style.configure("Accent.TButton", background=ACCENT, foreground="#1e1e2e",
                        font=("Segoe UI", 10, "bold"), relief="flat")
        style.map("Accent.TButton", background=[("active", ACCENT2)])
        style.configure("Danger.TButton", background="#f38ba8", foreground="#1e1e2e",
                        font=("Segoe UI", 10, "bold"), relief="flat")
        style.map("Danger.TButton", background=[("active", "#eba0ac")])
        style.configure("Ghost.TButton", background=SURFACE, foreground=FG,
                        font=("Segoe UI", 9), relief="flat")
        style.map("Ghost.TButton", background=[("active", ENTRY_BG)])

        self.BG = BG; self.SURFACE = SURFACE; self.ACCENT = ACCENT
        self.FG = FG; self.ENTRY_BG = ENTRY_BG

    # ───────────────────────────── UI ────────────────────────────────────────
    def _build_ui(self):
        # ── encabezado ──
        hdr = tk.Frame(self.root, bg="#181825", pady=12)
        hdr.pack(fill="x")
        tk.Label(hdr, text="💰 Control de Gastos Personales",
                 font=("Segoe UI", 16, "bold"), bg="#181825", fg=self.ACCENT).pack(side="left", padx=20)
        self.lbl_total_hdr = tk.Label(hdr, text="Total: RD$ 0.00",
                                      font=("Segoe UI", 12), bg="#181825", fg="#a6e3a1")
        self.lbl_total_hdr.pack(side="right", padx=20)

        # ── notebook ──
        nb = ttk.Notebook(self.root)
        nb.pack(fill="both", expand=True, padx=10, pady=10)

        self.tab_gastos = ttk.Frame(nb)
        self.tab_cats   = ttk.Frame(nb)
        nb.add(self.tab_gastos, text="  💸 Gastos  ")
        nb.add(self.tab_cats,   text="  🏷️ Categorías  ")

        self._build_tab_gastos()
        self._build_tab_categorias()

    # ───────────────────── TAB GASTOS ────────────────────────────────────────
    def _build_tab_gastos(self):
        parent = self.tab_gastos
        parent.configure(style="TFrame")
        parent.columnconfigure(0, weight=0, minsize=320)
        parent.columnconfigure(1, weight=1)
        parent.rowconfigure(0, weight=1)

        # ── panel izquierdo (formulario) ──
        left = tk.Frame(parent, bg=self.SURFACE, padx=18, pady=18)
        left.grid(row=0, column=0, sticky="nsew", padx=(8, 4), pady=8)

        self._lbl_form_gasto = tk.Label(left, text="➕ Registrar Gasto",
                                        font=("Segoe UI", 12, "bold"),
                                        bg=self.SURFACE, fg=self.ACCENT)
        self._lbl_form_gasto.grid(row=0, column=0, columnspan=2, pady=(0, 12), sticky="w")

        campos = [
            ("Descripción:",    "entry",    "_ent_desc"),
            ("Monto (RD$):",    "entry",    "_ent_monto"),
            ("Fecha:",          "date",     "_ent_fecha"),
            ("Categoría:",      "combo",    "_cmb_cat"),
            ("Notas:",          "entry",    "_ent_notas"),
        ]
        for i, (lbl, tipo, attr) in enumerate(campos, start=1):
            tk.Label(left, text=lbl, bg=self.SURFACE, fg=self.FG,
                     font=("Segoe UI", 9)).grid(row=i, column=0, sticky="w", pady=4)
            if tipo == "entry":
                w = ttk.Entry(left, width=24)
            elif tipo == "date":
                if CALENDAR_DISPONIBLE:
                    w = DateEntry(left, width=22, background="#313244",
                                  foreground="white", borderwidth=0,
                                  date_pattern="yyyy-mm-dd")
                else:
                    w = ttk.Entry(left, width=24)
                    w.insert(0, date.today().isoformat())
            else:
                w = ttk.Combobox(left, width=22, state="readonly")
            w.grid(row=i, column=1, sticky="ew", pady=4, padx=(8, 0))
            setattr(self, attr, w)

        # Botones formulario
        btn_frame = tk.Frame(left, bg=self.SURFACE)
        btn_frame.grid(row=len(campos)+1, column=0, columnspan=2, pady=(14, 0), sticky="ew")
        self._btn_guardar_gasto = ttk.Button(btn_frame, text="Guardar Gasto",
                                              style="Accent.TButton",
                                              command=self._guardar_gasto)
        self._btn_guardar_gasto.pack(fill="x", pady=(0, 6))
        self._btn_cancelar_gasto = ttk.Button(btn_frame, text="Cancelar edición",
                                               style="Ghost.TButton",
                                               command=self._cancelar_gasto)
        self._btn_cancelar_gasto.pack(fill="x")
        self._btn_cancelar_gasto.pack_forget()

        # ── panel derecho (tabla + filtros) ──
        right = tk.Frame(parent, bg=self.BG)
        right.grid(row=0, column=1, sticky="nsew", padx=(4, 8), pady=8)
        right.rowconfigure(1, weight=1)
        right.columnconfigure(0, weight=1)

        # filtros
        filt = tk.Frame(right, bg=self.SURFACE, padx=12, pady=8)
        filt.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        filt.columnconfigure(1, weight=1)
        filt.columnconfigure(3, weight=1)

        tk.Label(filt, text="Categoría:", bg=self.SURFACE, fg=self.FG,
                 font=("Segoe UI", 9)).grid(row=0, column=0, padx=(0, 6))
        self._cmb_filtro_cat = ttk.Combobox(filt, width=18, state="readonly")
        self._cmb_filtro_cat.grid(row=0, column=1, sticky="ew", padx=(0, 16))

        tk.Label(filt, text="Desde:", bg=self.SURFACE, fg=self.FG,
                 font=("Segoe UI", 9)).grid(row=0, column=2, padx=(0, 6))
        if CALENDAR_DISPONIBLE:
            self._date_desde = DateEntry(filt, width=12, date_pattern="yyyy-mm-dd")
        else:
            self._date_desde = ttk.Entry(filt, width=12)
        self._date_desde.grid(row=0, column=3, sticky="ew", padx=(0, 8))

        tk.Label(filt, text="Hasta:", bg=self.SURFACE, fg=self.FG,
                 font=("Segoe UI", 9)).grid(row=0, column=4, padx=(0, 6))
        if CALENDAR_DISPONIBLE:
            self._date_hasta = DateEntry(filt, width=12, date_pattern="yyyy-mm-dd")
        else:
            self._date_hasta = ttk.Entry(filt, width=12)
        self._date_hasta.grid(row=0, column=5, sticky="ew", padx=(0, 8))

        ttk.Button(filt, text="Filtrar",  style="Accent.TButton",
                   command=self._filtrar_gastos).grid(row=0, column=6, padx=(0, 4))
        ttk.Button(filt, text="✕ Limpiar", style="Ghost.TButton",
                   command=self._limpiar_filtros).grid(row=0, column=7)

        # treeview
        cols = ("Descripción", "Categoría", "Fecha", "Monto", "Notas")
        tree_wrap = tk.Frame(right, bg=self.BG)
        tree_wrap.grid(row=1, column=0, sticky="nsew")
        tree_wrap.rowconfigure(0, weight=1)
        tree_wrap.columnconfigure(0, weight=1)

        self._tree_gastos = ttk.Treeview(tree_wrap, columns=cols, show="headings",
                                          selectmode="browse")
        widths = {"Descripción": 200, "Categoría": 120, "Fecha": 95, "Monto": 90, "Notas": 160}
        for c in cols:
            self._tree_gastos.heading(c, text=c)
            self._tree_gastos.column(c, width=widths[c], minwidth=60)
        sb = ttk.Scrollbar(tree_wrap, orient="vertical", command=self._tree_gastos.yview)
        self._tree_gastos.configure(yscrollcommand=sb.set)
        self._tree_gastos.grid(row=0, column=0, sticky="nsew")
        sb.grid(row=0, column=1, sticky="ns")

        # barra inferior
        bot = tk.Frame(right, bg=self.SURFACE, padx=12, pady=8)
        bot.grid(row=2, column=0, sticky="ew", pady=(6, 0))

        ttk.Button(bot, text="✏️ Editar",   style="Ghost.TButton",
                   command=self._editar_gasto_seleccionado).pack(side="left", padx=(0, 6))
        ttk.Button(bot, text="🗑️ Eliminar", style="Danger.TButton",
                   command=self._eliminar_gasto_seleccionado).pack(side="left")

        self.lbl_total_tabla = tk.Label(bot, text="Total mostrado: RD$ 0.00",
                                         font=("Segoe UI", 10, "bold"),
                                         bg=self.SURFACE, fg="#a6e3a1")
        self.lbl_total_tabla.pack(side="right")

    # ───────────────────── TAB CATEGORÍAS ────────────────────────────────────
    def _build_tab_categorias(self):
        parent = self.tab_cats
        parent.columnconfigure(0, weight=0, minsize=300)
        parent.columnconfigure(1, weight=1)
        parent.rowconfigure(0, weight=1)

        # formulario
        left = tk.Frame(parent, bg=self.SURFACE, padx=18, pady=18)
        left.grid(row=0, column=0, sticky="nsew", padx=(8, 4), pady=8)

        self._lbl_form_cat = tk.Label(left, text="➕ Nueva Categoría",
                                      font=("Segoe UI", 12, "bold"),
                                      bg=self.SURFACE, fg=self.ACCENT)
        self._lbl_form_cat.grid(row=0, column=0, columnspan=2, pady=(0, 12), sticky="w")

        tk.Label(left, text="Nombre:", bg=self.SURFACE, fg=self.FG,
                 font=("Segoe UI", 9)).grid(row=1, column=0, sticky="w", pady=4)
        self._ent_cat_nombre = ttk.Entry(left, width=24)
        self._ent_cat_nombre.grid(row=1, column=1, sticky="ew", pady=4, padx=(8, 0))

        tk.Label(left, text="Descripción:", bg=self.SURFACE, fg=self.FG,
                 font=("Segoe UI", 9)).grid(row=2, column=0, sticky="w", pady=4)
        self._ent_cat_desc = ttk.Entry(left, width=24)
        self._ent_cat_desc.grid(row=2, column=1, sticky="ew", pady=4, padx=(8, 0))

        btn_f = tk.Frame(left, bg=self.SURFACE)
        btn_f.grid(row=3, column=0, columnspan=2, pady=(14, 0), sticky="ew")
        self._btn_guardar_cat = ttk.Button(btn_f, text="Guardar Categoría",
                                            style="Accent.TButton",
                                            command=self._guardar_categoria)
        self._btn_guardar_cat.pack(fill="x", pady=(0, 6))
        self._btn_cancelar_cat = ttk.Button(btn_f, text="Cancelar edición",
                                             style="Ghost.TButton",
                                             command=self._cancelar_cat)
        self._btn_cancelar_cat.pack(fill="x")
        self._btn_cancelar_cat.pack_forget()

        # lista
        right = tk.Frame(parent, bg=self.BG)
        right.grid(row=0, column=1, sticky="nsew", padx=(4, 8), pady=8)
        right.rowconfigure(0, weight=1)
        right.columnconfigure(0, weight=1)

        cols = ("ID", "Nombre", "Descripción")
        self._tree_cats = ttk.Treeview(right, columns=cols, show="headings",
                                        selectmode="browse")
        self._tree_cats.column("ID",          width=0,   minwidth=0, stretch=False)
        self._tree_cats.column("Nombre",      width=180, minwidth=100)
        self._tree_cats.column("Descripción", width=360, minwidth=100)
        for c in cols:
            self._tree_cats.heading(c, text=c)
        self._tree_cats.grid(row=0, column=0, sticky="nsew")
        sb2 = ttk.Scrollbar(right, orient="vertical", command=self._tree_cats.yview)
        self._tree_cats.configure(yscrollcommand=sb2.set)
        sb2.grid(row=0, column=1, sticky="ns")

        bot = tk.Frame(right, bg=self.SURFACE, padx=12, pady=8)
        bot.grid(row=1, column=0, sticky="ew", pady=(6, 0))
        ttk.Button(bot, text="✏️ Editar",   style="Ghost.TButton",
                   command=self._editar_cat_seleccionada).pack(side="left", padx=(0, 6))
        ttk.Button(bot, text="🗑️ Eliminar", style="Danger.TButton",
                   command=self._eliminar_cat_seleccionada).pack(side="left")

    # ─────────────────────── CARGA DE DATOS ──────────────────────────────────
    def _cargar_datos(self):
        self._refrescar_categorias()
        self._refrescar_gastos()

    def _refrescar_categorias(self):
        cats = self.cat_service.listar_categorias()

        # actualizar combobox del formulario de gastos
        nombres = [c.nombre for c in cats]
        self._cmb_cat["values"] = nombres

        # actualizar combobox de filtro
        self._cmb_filtro_cat["values"] = ["Todas"] + nombres
        self._cmb_filtro_cat.set("Todas")

        # actualizar treeview categorías
        for row in self._tree_cats.get_children():
            self._tree_cats.delete(row)
        for c in cats:
            self._tree_cats.insert("", "end", values=(c.id, c.nombre, c.descripcion))

    def _refrescar_gastos(self, gastos=None):
        if gastos is None:
            gastos = self.gas_service.listar_gastos()
        cats = {c.id: c.nombre for c in self.cat_service.listar_categorias()}

        for row in self._tree_gastos.get_children():
            self._tree_gastos.delete(row)

        total = 0.0
        for g in gastos:
            total += g.monto
            self._tree_gastos.insert("", "end", iid=g.id, values=(
                g.descripcion,
                cats.get(g.categoria_id, "—"),
                g.fecha,
                f"RD$ {g.monto:,.2f}",
                g.notas
            ))

        self.lbl_total_tabla.config(text=f"Total mostrado: RD$ {total:,.2f}")
        self.lbl_total_hdr.config(text=f"Total: RD$ {self.gas_service.total_gastos():,.2f}")

    # ─────────────────── ACCIONES GASTOS ─────────────────────────────────────
    def _guardar_gasto(self):
        desc    = self._ent_desc.get().strip()
        monto   = self._ent_monto.get().strip()
        fecha   = self._get_fecha(self._ent_fecha)
        notas   = self._ent_notas.get().strip()
        cat_nom = self._cmb_cat.get()

        # obtener categoria_id por nombre
        cats = self.cat_service.listar_categorias()
        cat  = next((c for c in cats if c.nombre == cat_nom), None)
        if not cat:
            messagebox.showwarning("Atención", "Selecciona una categoría válida.")
            return

        try:
            if self._edit_gasto_id:
                self.gas_service.actualizar_gasto(
                    self._edit_gasto_id, desc, monto, fecha, cat.id, notas)
                messagebox.showinfo("Éxito", "Gasto actualizado.")
            else:
                self.gas_service.crear_gasto(desc, monto, fecha, cat.id, notas)
                messagebox.showinfo("Éxito", "Gasto registrado.")
        except ValueError as e:
            messagebox.showerror("Error", str(e))
            return

        self._limpiar_form_gasto()
        self._refrescar_gastos()

    def _editar_gasto_seleccionado(self):
        sel = self._tree_gastos.selection()
        if not sel:
            messagebox.showinfo("Atención", "Selecciona un gasto de la tabla.")
            return
        gasto_id = sel[0]
        g = self.gas_service.obtener_gasto(gasto_id)
        if not g:
            return
        cats   = self.cat_service.listar_categorias()
        cat    = next((c for c in cats if c.id == g.categoria_id), None)

        self._ent_desc.delete(0, "end"); self._ent_desc.insert(0, g.descripcion)
        self._ent_monto.delete(0, "end"); self._ent_monto.insert(0, str(g.monto))
        self._set_fecha(self._ent_fecha, g.fecha)
        self._cmb_cat.set(cat.nombre if cat else "")
        self._ent_notas.delete(0, "end"); self._ent_notas.insert(0, g.notas)

        self._edit_gasto_id = gasto_id
        self._lbl_form_gasto.config(text="✏️ Editar Gasto")
        self._btn_guardar_gasto.config(text="Actualizar Gasto")
        self._btn_cancelar_gasto.pack(fill="x")

    def _eliminar_gasto_seleccionado(self):
        sel = self._tree_gastos.selection()
        if not sel:
            messagebox.showinfo("Atención", "Selecciona un gasto de la tabla.")
            return
        if not messagebox.askyesno("Confirmar", "¿Eliminar el gasto seleccionado?"):
            return
        try:
            self.gas_service.eliminar_gasto(sel[0])
        except ValueError as e:
            messagebox.showerror("Error", str(e))
            return
        self._refrescar_gastos()

    def _cancelar_gasto(self):
        self._limpiar_form_gasto()

    def _limpiar_form_gasto(self):
        self._edit_gasto_id = None
        self._ent_desc.delete(0, "end")
        self._ent_monto.delete(0, "end")
        self._set_fecha(self._ent_fecha, date.today().isoformat())
        self._cmb_cat.set("")
        self._ent_notas.delete(0, "end")
        self._lbl_form_gasto.config(text="➕ Registrar Gasto")
        self._btn_guardar_gasto.config(text="Guardar Gasto")
        self._btn_cancelar_gasto.pack_forget()

    # ─────────────────── ACCIONES CATEGORÍAS ─────────────────────────────────
    def _guardar_categoria(self):
        nombre = self._ent_cat_nombre.get().strip()
        desc   = self._ent_cat_desc.get().strip()
        try:
            if self._edit_cat_id:
                self.cat_service.actualizar_categoria(self._edit_cat_id, nombre, desc)
                messagebox.showinfo("Éxito", "Categoría actualizada.")
            else:
                self.cat_service.crear_categoria(nombre, desc)
                messagebox.showinfo("Éxito", "Categoría creada.")
        except ValueError as e:
            messagebox.showerror("Error", str(e))
            return
        self._cancelar_cat()
        self._refrescar_categorias()

    def _editar_cat_seleccionada(self):
        sel = self._tree_cats.selection()
        if not sel:
            messagebox.showinfo("Atención", "Selecciona una categoría.")
            return
        vals = self._tree_cats.item(sel[0], "values")
        cat_id, nombre, desc = vals[0], vals[1], vals[2]
        self._ent_cat_nombre.delete(0, "end"); self._ent_cat_nombre.insert(0, nombre)
        self._ent_cat_desc.delete(0, "end");   self._ent_cat_desc.insert(0, desc)
        self._edit_cat_id = cat_id
        self._lbl_form_cat.config(text="✏️ Editar Categoría")
        self._btn_guardar_cat.config(text="Actualizar Categoría")
        self._btn_cancelar_cat.pack(fill="x")

    def _eliminar_cat_seleccionada(self):
        sel = self._tree_cats.selection()
        if not sel:
            messagebox.showinfo("Atención", "Selecciona una categoría.")
            return
        cat_id = self._tree_cats.item(sel[0], "values")[0]
        if not messagebox.askyesno("Confirmar", "¿Eliminar esta categoría?"):
            return
        try:
            self.cat_service.eliminar_categoria(cat_id, self.gas_repo)
        except ValueError as e:
            messagebox.showerror("Error", str(e))
            return
        self._refrescar_categorias()
        self._refrescar_gastos()

    def _cancelar_cat(self):
        self._edit_cat_id = None
        self._ent_cat_nombre.delete(0, "end")
        self._ent_cat_desc.delete(0, "end")
        self._lbl_form_cat.config(text="➕ Nueva Categoría")
        self._btn_guardar_cat.config(text="Guardar Categoría")
        self._btn_cancelar_cat.pack_forget()

    # ─────────────────────── FILTROS ─────────────────────────────────────────
    def _filtrar_gastos(self):
        cat_nom = self._cmb_filtro_cat.get()
        desde   = self._get_fecha(self._date_desde)
        hasta   = self._get_fecha(self._date_hasta)

        cats = self.cat_service.listar_categorias()
        cat  = next((c for c in cats if c.nombre == cat_nom), None)

        try:
            if cat and desde and hasta:
                gastos = self.gas_service.filtrar_por_categoria_y_fecha(cat.id, desde, hasta)
            elif cat:
                gastos = self.gas_service.filtrar_por_categoria(cat.id)
            elif desde and hasta:
                gastos = self.gas_service.filtrar_por_fecha(desde, hasta)
            else:
                gastos = self.gas_service.listar_gastos()
        except ValueError as e:
            messagebox.showerror("Error de filtro", str(e))
            return
        self._refrescar_gastos(gastos)

    def _limpiar_filtros(self):
        self._cmb_filtro_cat.set("Todas")
        if not CALENDAR_DISPONIBLE:
            self._date_desde.delete(0, "end")
            self._date_hasta.delete(0, "end")
        self._refrescar_gastos()

    # ─────────────────────── HELPERS ─────────────────────────────────────────
    def _get_fecha(self, widget) -> str:
        if CALENDAR_DISPONIBLE:
            try:
                return widget.get_date().isoformat()
            except Exception:
                return ""
        return widget.get().strip()

    def _set_fecha(self, widget, valor: str):
        if CALENDAR_DISPONIBLE:
            try:
                from datetime import date as d
                widget.set_date(d.fromisoformat(valor))
            except Exception:
                pass
        else:
            widget.delete(0, "end")
            widget.insert(0, valor)