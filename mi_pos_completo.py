import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import sqlite3
from datetime import datetime
import os
import sys
import hashlib

# ===================== COLORES PROFESIONALES =====================
COLOR_FONDO = "#f0f4f8"          # gris azulado muy claro
COLOR_ENCABEZADO = "#1a365d"     # azul marino oscuro
COLOR_BOTON_AGREGAR = "#2f855a"  # verde elegante
COLOR_BOTON_MODIFICAR = "#2b6cb0" # azul medio
COLOR_BOTON_ELIMINAR = "#c53030" # rojo vino
COLOR_BOTON_BUSCAR = "#c05621"   # naranja tostado
COLOR_BOTON_VENTA = "#2a4365"    # azul acero
COLOR_TOTAL = "#276749"          # verde musgo
COLOR_BOTON_SECUNDARIO = "#4a5568" # gris pizarra
COLOR_BOTON_REPORTE = "#718096"  # gris medio

# Hover (un poco más claro)
HOVER_AGREGAR = "#38a169"
HOVER_MODIFICAR = "#3182ce"
HOVER_ELIMINAR = "#e53e3e"
HOVER_BUSCAR = "#dd6b20"
HOVER_VENTA = "#2c5282"
HOVER_SECUNDARIO = "#718096"
HOVER_REPORTE = "#a0aec0"

# Archivos de configuración
PASSWORD_FILE = "password.hash"
IVA_FILE = "iva_config.txt"

# ===================== CLASE BOTÓN REDONDEADO =====================
class RoundedButton(tk.Canvas):
    """Botón con esquinas redondeadas y efecto hover"""
    def __init__(self, parent, text, command, bg, hover_bg, width=120, height=36, radius=10,
                 font=('Segoe UI', 10, 'bold'), fg='white', *args, **kwargs):
        super().__init__(parent, width=width, height=height, highlightthickness=0,
                         bg=parent['bg'], *args, **kwargs)
        self.command = command
        self.bg = bg
        self.hover_bg = hover_bg
        self.current_color = bg
        self.radius = radius
        self.font = font
        self.fg = fg
        self.text = text

        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        self.bind("<Button-1>", self.on_click)

        self.draw()

    def draw(self):
        self.delete("all")
        self.create_rounded_rect(2, 2, self.winfo_reqwidth()-2, self.winfo_reqheight()-2,
                                 self.radius, fill=self.current_color, outline="")
        self.create_text(self.winfo_reqwidth()/2, self.winfo_reqheight()/2,
                         text=self.text, fill=self.fg, font=self.font)

    def create_rounded_rect(self, x1, y1, x2, y2, r, **kwargs):
        points = [x1+r, y1,
                  x1+r, y1,
                  x2-r, y1,
                  x2-r, y1,
                  x2, y1,
                  x2, y1+r,
                  x2, y2-r,
                  x2, y2,
                  x2-r, y2,
                  x2-r, y2,
                  x1+r, y2,
                  x1+r, y2,
                  x1, y2,
                  x1, y2-r,
                  x1, y1+r,
                  x1, y1]
        self.create_polygon(points, smooth=True, **kwargs)

    def on_enter(self, event):
        self.current_color = self.hover_bg
        self.draw()

    def on_leave(self, event):
        self.current_color = self.bg
        self.draw()

    def on_click(self, event):
        if self.command:
            self.command()

# ===================== SISTEMA DE LOGIN =====================
def login():
    """Verifica la contraseña o la configura en el primer inicio"""
    if os.path.exists(PASSWORD_FILE):
        password = simpledialog.askstring("Acceso", "Ingrese la contraseña:", show='*')
        if password is None:
            return False
        with open(PASSWORD_FILE, 'r') as f:
            stored_hash = f.read().strip()
        input_hash = hashlib.sha256(password.encode()).hexdigest()
        if input_hash != stored_hash:
            messagebox.showerror("Error", "Contraseña incorrecta")
            return False
        return True
    else:
        while True:
            password = simpledialog.askstring("Configurar acceso",
                                              "Cree una contraseña (mín. 4 caracteres):", show='*')
            if password is None:
                return False
            if len(password) < 4:
                messagebox.showwarning("Contraseña débil", "Debe tener al menos 4 caracteres.")
                continue
            confirm = simpledialog.askstring("Confirmar", "Confirme la contraseña:", show='*')
            if confirm is None:
                return False
            if password != confirm:
                messagebox.showerror("Error", "Las contraseñas no coinciden.")
                continue
            hash_val = hashlib.sha256(password.encode()).hexdigest()
            with open(PASSWORD_FILE, 'w') as f:
                f.write(hash_val)
            messagebox.showinfo("Éxito", "Contraseña guardada correctamente.")
            return True

# ===================== SISTEMA PRINCIPAL =====================
class SistemaPOS:
    def __init__(self, root):
        self.root = root
        self.root.title("LOS BUENA ONDA - Punto de Venta")
        self.root.geometry("1300x750")
        self.root.configure(bg=COLOR_FONDO)
        self.root.minsize(1200, 700)

        # Estilo de pestañas
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TNotebook.Tab', font=('Segoe UI', 10, 'bold'), padding=[15, 6],
                        background='white', foreground=COLOR_ENCABEZADO)
        style.map('TNotebook.Tab', background=[('selected', COLOR_ENCABEZADO)],
                  foreground=[('selected', 'white')])

        # Variables
        self.carrito = []
        self.total_venta = 0.0
        self.iva_porcentaje = self.cargar_iva()  # porcentaje de IVA (ej. 16)

        # Base de datos
        self.conn = sqlite3.connect('buena_onda.db')
        self.cursor = self.conn.cursor()
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS productos
                            (id INTEGER PRIMARY KEY AUTOINCREMENT,
                            nombre TEXT NOT NULL,
                            precio REAL NOT NULL,
                            stock INTEGER NOT NULL)''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS ventas
                            (id INTEGER PRIMARY KEY AUTOINCREMENT,
                            fecha TEXT NOT NULL,
                            total REAL NOT NULL)''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS detalles_venta
                            (id INTEGER PRIMARY KEY AUTOINCREMENT,
                            venta_id INTEGER,
                            producto_id INTEGER,
                            nombre TEXT,
                            precio REAL,
                            cantidad INTEGER,
                            subtotal REAL)''')
        self.conn.commit()

        # Construcción de interfaz
        self.crear_interfaz()
        self.mostrar_productos()
        self.actualizar_reloj()

    def cargar_iva(self):
        """Carga el porcentaje de IVA desde archivo, o retorna 16 por defecto"""
        if os.path.exists(IVA_FILE):
            with open(IVA_FILE, 'r') as f:
                try:
                    return float(f.read().strip())
                except:
                    return 16.0
        return 16.0

    def guardar_iva(self, valor):
        """Guarda el nuevo porcentaje de IVA en archivo"""
        with open(IVA_FILE, 'w') as f:
            f.write(str(valor))

    def actualizar_reloj(self):
        ahora = datetime.now()
        fecha_hora = ahora.strftime("%d/%m/%Y  |  %I:%M:%S %p")
        self.reloj_label.config(text=f"📅 {fecha_hora}")
        self.root.after(1000, self.actualizar_reloj)

    def crear_interfaz(self):
        # Frame superior
        frame_superior = tk.Frame(self.root, bg=COLOR_ENCABEZADO, height=80)
        frame_superior.pack(fill=tk.X)

        titulo = tk.Label(frame_superior, text="TIENDA LOS BUENA ONDA",
                         font=('Segoe UI', 26, 'bold'), bg=COLOR_ENCABEZADO, fg='white')
        titulo.pack(side=tk.LEFT, padx=20, pady=12)

        # Botón de configuración (tres puntitos)
        btn_config = tk.Button(frame_superior, text="⚙️", font=('Segoe UI', 14, 'bold'),
                               bg=COLOR_ENCABEZADO, fg='white', relief=tk.FLAT,
                               bd=0, activebackground=COLOR_ENCABEZADO, activeforeground='#ecc94b',
                               command=self.abrir_configuracion)
        btn_config.pack(side=tk.RIGHT, padx=(0,20), pady=15)

        self.reloj_label = tk.Label(frame_superior, text="", font=('Segoe UI', 12, 'bold'),
                                    bg=COLOR_ENCABEZADO, fg='#ecc94b')
        self.reloj_label.pack(side=tk.RIGHT, padx=20, pady=15)

        subtitulo = tk.Label(self.root, text="Sistema de inventario y ventas · Profesional",
                            font=('Segoe UI', 11), bg=COLOR_ENCABEZADO, fg='#cbd5e0')
        subtitulo.pack(fill=tk.X)

        # Notebook (pestañas)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        self.frame_productos = ttk.Frame(self.notebook)
        self.frame_ventas = ttk.Frame(self.notebook)
        self.frame_reportes = ttk.Frame(self.notebook)
        self.notebook.add(self.frame_productos, text="📦 INVENTARIO")
        self.notebook.add(self.frame_ventas, text="💰 PUNTO DE VENTA")
        self.notebook.add(self.frame_reportes, text="📊 REPORTES")

        self.construir_productos()
        self.construir_ventas()
        self.construir_reportes()

    def abrir_configuracion(self):
        """Ventana de configuración: cambiar contraseña o IVA"""
        config_win = tk.Toplevel(self.root)
        config_win.title("Configuración")
        config_win.geometry("300x200")
        config_win.configure(bg='white')
        config_win.resizable(False, False)
        config_win.transient(self.root)
        config_win.grab_set()

        tk.Label(config_win, text="⚙️ Ajustes del sistema", font=('Segoe UI', 12, 'bold'),
                 bg='white', fg=COLOR_ENCABEZADO).pack(pady=15)

        RoundedButton(config_win, "🔒 Cambiar contraseña", self.cambiar_password,
                     COLOR_BOTON_MODIFICAR, HOVER_MODIFICAR, width=180, height=36).pack(pady=5)
        RoundedButton(config_win, "💰 Configurar IVA", self.configurar_iva,
                     COLOR_BOTON_VENTA, HOVER_VENTA, width=180, height=36).pack(pady=5)

    def cambiar_password(self):
        """Cambia la contraseña actual"""
        if not os.path.exists(PASSWORD_FILE):
            messagebox.showwarning("Sin contraseña", "No hay contraseña almacenada.")
            return
        actual = simpledialog.askstring("Verificar", "Ingrese la contraseña actual:", show='*')
        if actual is None:
            return
        with open(PASSWORD_FILE, 'r') as f:
            stored_hash = f.read().strip()
        if hashlib.sha256(actual.encode()).hexdigest() != stored_hash:
            messagebox.showerror("Error", "Contraseña actual incorrecta")
            return
        nueva = simpledialog.askstring("Nueva", "Ingrese la nueva contraseña (mín. 4):", show='*')
        if nueva is None or len(nueva) < 4:
            messagebox.showwarning("Inválida", "Debe tener al menos 4 caracteres.")
            return
        confirm = simpledialog.askstring("Confirmar", "Confirme la nueva contraseña:", show='*')
        if confirm != nueva:
            messagebox.showerror("Error", "Las contraseñas no coinciden.")
            return
        new_hash = hashlib.sha256(nueva.encode()).hexdigest()
        with open(PASSWORD_FILE, 'w') as f:
            f.write(new_hash)
        messagebox.showinfo("Éxito", "Contraseña actualizada correctamente.")

    def configurar_iva(self):
        """Permite cambiar el porcentaje de IVA"""
        actual = simpledialog.askfloat("IVA", f"Ingrese el porcentaje de IVA (actual: {self.iva_porcentaje}%):",
                                       minvalue=0, maxvalue=100)
        if actual is not None:
            self.iva_porcentaje = actual
            self.guardar_iva(actual)
            messagebox.showinfo("IVA actualizado", f"El IVA se ha fijado en {actual}%.")

    def construir_productos(self):
        main_frame = tk.Frame(self.frame_productos, bg=COLOR_FONDO)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=25, pady=25)

        titulo = tk.Label(main_frame, text="Administración de Productos",
                         font=('Segoe UI', 18, 'bold'), bg=COLOR_FONDO, fg=COLOR_ENCABEZADO)
        titulo.pack(anchor=tk.W, pady=(0, 15))

        # Panel de búsqueda avanzada
        frame_busqueda_avanzada = tk.Frame(main_frame, bg='white', relief=tk.RAISED, bd=2)
        frame_busqueda_avanzada.pack(fill=tk.X, pady=(0, 15))

        tk.Label(frame_busqueda_avanzada, text="Rango de precio:", font=('Segoe UI', 10, 'bold'),
                 bg='white').pack(side=tk.LEFT, padx=15, pady=8)
        tk.Label(frame_busqueda_avanzada, text="Min:", bg='white').pack(side=tk.LEFT, padx=(10,2))
        self.precio_min_entry = tk.Entry(frame_busqueda_avanzada, width=7, font=('Segoe UI', 10))
        self.precio_min_entry.pack(side=tk.LEFT, padx=2)
        tk.Label(frame_busqueda_avanzada, text="Max:", bg='white').pack(side=tk.LEFT, padx=2)
        self.precio_max_entry = tk.Entry(frame_busqueda_avanzada, width=7, font=('Segoe UI', 10))
        self.precio_max_entry.pack(side=tk.LEFT, padx=2)
        RoundedButton(frame_busqueda_avanzada, "🔍 Filtrar", self.buscar_productos_por_precio,
                     COLOR_BOTON_BUSCAR, HOVER_BUSCAR, width=100, height=32).pack(side=tk.LEFT, padx=8)
        RoundedButton(frame_busqueda_avanzada, "🔄 Mostrar todos", self.mostrar_productos,
                     COLOR_BOTON_SECUNDARIO, HOVER_SECUNDARIO, width=140, height=32).pack(side=tk.LEFT, padx=5)

        # Frame de entrada de datos
        card_frame = tk.Frame(main_frame, bg='white', relief=tk.RAISED, bd=2)
        card_frame.pack(fill=tk.X, pady=(0, 20))

        tk.Label(card_frame, text="Nombre:", font=('Segoe UI', 10, 'bold'), bg='white').grid(
            row=0, column=0, padx=15, pady=12, sticky=tk.W)
        self.nombre_entry = tk.Entry(card_frame, font=('Segoe UI', 11), width=28, bg='#fafafa',
                                     relief=tk.FLAT, bd=1)
        self.nombre_entry.grid(row=0, column=1, padx=10, pady=12)

        tk.Label(card_frame, text="Precio ($):", font=('Segoe UI', 10, 'bold'), bg='white').grid(
            row=0, column=2, padx=15, pady=12, sticky=tk.W)
        self.precio_entry = tk.Entry(card_frame, font=('Segoe UI', 11), width=12, bg='#fafafa',
                                     relief=tk.FLAT, bd=1)
        self.precio_entry.grid(row=0, column=3, padx=10, pady=12)

        tk.Label(card_frame, text="Stock:", font=('Segoe UI', 10, 'bold'), bg='white').grid(
            row=0, column=4, padx=15, pady=12, sticky=tk.W)
        self.stock_entry = tk.Entry(card_frame, font=('Segoe UI', 11), width=10, bg='#fafafa',
                                    relief=tk.FLAT, bd=1)
        self.stock_entry.grid(row=0, column=5, padx=10, pady=12)

        # Botones de acción con redondeo y anchos ajustados
        botones_data = [
            ("➕ AGREGAR", self.agregar_producto, COLOR_BOTON_AGREGAR, HOVER_AGREGAR, 120),
            ("✏️ MODIFICAR", self.modificar_producto, COLOR_BOTON_MODIFICAR, HOVER_MODIFICAR, 130),
            ("🔍 BUSCAR", self.buscar_producto, COLOR_BOTON_BUSCAR, HOVER_BUSCAR, 110),
            ("🗑️ ELIMINAR", self.eliminar_producto, COLOR_BOTON_ELIMINAR, HOVER_ELIMINAR, 120),
            ("🔄 ACTUALIZAR", self.mostrar_productos, COLOR_BOTON_SECUNDARIO, HOVER_SECUNDARIO, 130),
            ("📈 ESTADÍSTICAS", self.mostrar_estadisticas, COLOR_BOTON_VENTA, HOVER_VENTA, 140),
            ("📎 EXPORTAR EXCEL", self.exportar_productos_excel, COLOR_BOTON_SECUNDARIO, HOVER_SECUNDARIO, 150)
        ]
        for i, (text, cmd, bg, hbg, w) in enumerate(botones_data):
            btn = RoundedButton(card_frame, text, cmd, bg, hbg, width=w, height=36)
            btn.grid(row=1, column=i, padx=6, pady=12)

        # Tabla de productos
        tabla_frame = tk.Frame(main_frame, bg='white', relief=tk.RAISED, bd=2)
        tabla_frame.pack(fill=tk.BOTH, expand=True)

        scroll_y = ttk.Scrollbar(tabla_frame, orient=tk.VERTICAL)
        scroll_x = ttk.Scrollbar(tabla_frame, orient=tk.HORIZONTAL)

        self.tree = ttk.Treeview(tabla_frame, columns=("ID", "Nombre", "Precio", "Stock"),
                                 show="headings", height=18,
                                 yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
        scroll_y.config(command=self.tree.yview)
        scroll_x.config(command=self.tree.xview)

        self.tree.heading("ID", text="ID")
        self.tree.heading("Nombre", text="PRODUCTO")
        self.tree.heading("Precio", text="PRECIO ($)")
        self.tree.heading("Stock", text="STOCK")
        self.tree.column("ID", width=70, anchor='center')
        self.tree.column("Nombre", width=440)
        self.tree.column("Precio", width=130, anchor='center')
        self.tree.column("Stock", width=110, anchor='center')

        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scroll_y.grid(row=0, column=1, sticky=(tk.N, tk.S))
        scroll_x.grid(row=1, column=0, sticky=(tk.W, tk.E))
        tabla_frame.columnconfigure(0, weight=1)
        tabla_frame.rowconfigure(0, weight=1)

        self.tree.bind('<<TreeviewSelect>>', self.seleccionar_producto)
        self.label_total = tk.Label(main_frame, text="Total de productos: 0",
                                    font=('Segoe UI', 10, 'italic'),
                                    bg=COLOR_FONDO, fg='#4a5568')
        self.label_total.pack(anchor=tk.W, pady=(12, 0))

    # ------------------------------------------------------------
    # Los métodos buscar_productos_por_precio, mostrar_estadisticas,
    # exportar_productos_excel se mantienen igual que antes...
    # (Se incluyen completos para evitar omisiones)
    # ------------------------------------------------------------
    def buscar_productos_por_precio(self):
        try:
            min_precio = float(self.precio_min_entry.get()) if self.precio_min_entry.get() else 0
            max_precio = float(self.precio_max_entry.get()) if self.precio_max_entry.get() else float('inf')
        except ValueError:
            messagebox.showerror("Error", "Ingrese valores numéricos válidos para el rango de precios.")
            return
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.cursor.execute("SELECT * FROM productos WHERE precio BETWEEN ? AND ? ORDER BY id",
                            (min_precio, max_precio))
        productos = self.cursor.fetchall()
        for producto in productos:
            self.tree.insert("", tk.END, values=producto)
        self.label_total.config(text=f"Productos encontrados: {len(productos)}")
        if not productos:
            messagebox.showinfo("Búsqueda", "No hay productos en ese rango de precios.")

    def mostrar_estadisticas(self):
        self.cursor.execute("SELECT SUM(total) FROM ventas")
        ventas_totales = self.cursor.fetchone()[0] or 0
        self.cursor.execute("SELECT COUNT(*) FROM productos WHERE stock < 5 AND stock > 0")
        stock_bajo = self.cursor.fetchone()[0]
        messagebox.showinfo("Estadísticas del negocio",
                            f"💰 Ventas totales acumuladas: ${ventas_totales:,.2f}\n"
                            f"⚠️ Productos con stock bajo (<5 unidades): {stock_bajo}")

    def exportar_productos_excel(self):
        try:
            import openpyxl
            from openpyxl.styles import Font, Alignment, PatternFill
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Productos"
            headers = ["ID", "Nombre", "Precio", "Stock"]
            header_fill = PatternFill(start_color=COLOR_ENCABEZADO, end_color=COLOR_ENCABEZADO, fill_type="solid")
            for col, header in enumerate(headers, 1):
                cell = ws.cell(row=1, column=col, value=header)
                cell.font = Font(bold=True, color="white", size=11)
                cell.fill = header_fill
                cell.alignment = Alignment(horizontal="center")
            self.cursor.execute("SELECT id, nombre, precio, stock FROM productos ORDER BY id")
            for row, prod in enumerate(self.cursor.fetchall(), 2):
                ws.cell(row=row, column=1, value=prod[0]).alignment = Alignment(horizontal="center")
                ws.cell(row=row, column=2, value=prod[1])
                ws.cell(row=row, column=3, value=prod[2]).alignment = Alignment(horizontal="center")
                ws.cell(row=row, column=4, value=prod[3]).alignment = Alignment(horizontal="center")
            ws.column_dimensions['A'].width = 8
            ws.column_dimensions['B'].width = 35
            ws.column_dimensions['C'].width = 12
            ws.column_dimensions['D'].width = 10
            wb.save("productos_buena_onda.xlsx")
            messagebox.showinfo("Exportar", "Productos exportados a 'productos_buena_onda.xlsx'")
        except ImportError:
            messagebox.showerror("Error", "No se encontró la librería openpyxl.\nInstálela con: pip install openpyxl")

    # ===================== PUNTO DE VENTA =====================
    def construir_ventas(self):
        main_frame = tk.Frame(self.frame_ventas, bg=COLOR_FONDO)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=25, pady=25)

        panel_izq = tk.Frame(main_frame, bg=COLOR_FONDO)
        panel_izq.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 12))
        panel_der = tk.Frame(main_frame, bg=COLOR_FONDO)
        panel_der.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(12, 0))

        # Card izquierda
        card_izq = tk.Frame(panel_izq, bg='white', relief=tk.RAISED, bd=2)
        card_izq.pack(fill=tk.BOTH, expand=True)
        tk.Label(card_izq, text="🛒 SELECCIONAR PRODUCTO", font=('Segoe UI', 14, 'bold'),
                 bg=COLOR_ENCABEZADO, fg='white', pady=12).pack(fill=tk.X)

        frame_buscar = tk.Frame(card_izq, bg='white', pady=12)
        frame_buscar.pack(fill=tk.X, padx=18, pady=10)
        tk.Label(frame_buscar, text="Buscar:", font=('Segoe UI', 10, 'bold'), bg='white').pack(side=tk.LEFT)
        self.buscar_venta_entry = tk.Entry(frame_buscar, font=('Segoe UI', 11), width=40)
        self.buscar_venta_entry.pack(side=tk.LEFT, padx=10)
        RoundedButton(frame_buscar, "🔍", self.buscar_producto_venta,
                     COLOR_BOTON_BUSCAR, HOVER_BUSCAR, width=42, height=32).pack(side=tk.LEFT)

        tk.Label(card_izq, text="Productos disponibles:", font=('Segoe UI', 10, 'bold'),
                 bg='white').pack(anchor=tk.W, padx=18, pady=(10,0))
        frame_lista = tk.Frame(card_izq, bg='white')
        frame_lista.pack(fill=tk.BOTH, expand=True, padx=18, pady=10)
        scroll_lista = tk.Scrollbar(frame_lista)
        self.lista_productos = tk.Listbox(frame_lista, height=12, font=('Segoe UI', 10),
                                          yscrollcommand=scroll_lista.set, bg='#fafafa')
        scroll_lista.config(command=self.lista_productos.yview)
        self.lista_productos.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll_lista.pack(side=tk.RIGHT, fill=tk.Y)

        frame_cantidad = tk.Frame(card_izq, bg='white', pady=12)
        frame_cantidad.pack(fill=tk.X, padx=18, pady=10)
        tk.Label(frame_cantidad, text="Cantidad:", font=('Segoe UI', 10, 'bold'), bg='white').pack(side=tk.LEFT)
        self.cantidad_entry = tk.Entry(frame_cantidad, width=8, font=('Segoe UI', 11))
        self.cantidad_entry.pack(side=tk.LEFT, padx=10)
        self.cantidad_entry.insert(0, "1")
        RoundedButton(frame_cantidad, "➕ AGREGAR AL CARRITO", self.agregar_al_carrito,
                     COLOR_BOTON_AGREGAR, HOVER_AGREGAR, width=190, height=36).pack(side=tk.LEFT, padx=12)

        # Card derecha (carrito)
        card_der = tk.Frame(panel_der, bg='white', relief=tk.RAISED, bd=2)
        card_der.pack(fill=tk.BOTH, expand=True)
        tk.Label(card_der, text="🛍️ CARRITO DE COMPRAS", font=('Segoe UI', 14, 'bold'),
                 bg=COLOR_ENCABEZADO, fg='white', pady=12).pack(fill=tk.X)

        frame_tabla_carrito = tk.Frame(card_der, bg='white')
        frame_tabla_carrito.pack(fill=tk.BOTH, expand=True, padx=18, pady=10)
        scroll_carrito_y = ttk.Scrollbar(frame_tabla_carrito, orient=tk.VERTICAL)
        scroll_carrito_x = ttk.Scrollbar(frame_tabla_carrito, orient=tk.HORIZONTAL)
        self.tabla_carrito = ttk.Treeview(frame_tabla_carrito,
                                          columns=("Producto", "Precio", "Cantidad", "Subtotal"),
                                          show="headings", height=8,
                                          yscrollcommand=scroll_carrito_y.set,
                                          xscrollcommand=scroll_carrito_x.set)
        self.tabla_carrito.heading("Producto", text="PRODUCTO")
        self.tabla_carrito.heading("Precio", text="P.UNIT ($)")
        self.tabla_carrito.heading("Cantidad", text="CANT")
        self.tabla_carrito.heading("Subtotal", text="SUBTOTAL ($)")
        for col in ("Producto", "Precio", "Cantidad", "Subtotal"):
            self.tabla_carrito.column(col, width=140 if col=="Producto" else 90, anchor='center')
        self.tabla_carrito.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scroll_carrito_y.grid(row=0, column=1, sticky=(tk.N, tk.S))
        scroll_carrito_x.grid(row=1, column=0, sticky=(tk.W, tk.E))
        frame_tabla_carrito.columnconfigure(0, weight=1)
        frame_tabla_carrito.rowconfigure(0, weight=1)

        frame_total = tk.Frame(card_der, bg=COLOR_TOTAL, pady=18)
        frame_total.pack(fill=tk.X, padx=18, pady=12)
        tk.Label(frame_total, text="TOTAL:", font=('Segoe UI', 18, 'bold'),
                 bg=COLOR_TOTAL, fg='white').pack(side=tk.LEFT, padx=20)
        self.total_label = tk.Label(frame_total, text="$0.00", font=('Segoe UI', 26, 'bold'),
                                    bg=COLOR_TOTAL, fg='#fbd38d')
        self.total_label.pack(side=tk.RIGHT, padx=20)

        frame_botones_carrito = tk.Frame(card_der, bg='white')
        frame_botones_carrito.pack(fill=tk.X, padx=18, pady=12)
        RoundedButton(frame_botones_carrito, "🗑️ ELIMINAR", self.eliminar_del_carrito,
                     COLOR_BOTON_ELIMINAR, HOVER_ELIMINAR, width=120, height=36).pack(side=tk.LEFT, padx=5)
        RoundedButton(frame_botones_carrito, "🔄 VACIAR", self.vaciar_carrito,
                     COLOR_BOTON_SECUNDARIO, HOVER_SECUNDARIO, width=110, height=36).pack(side=tk.LEFT, padx=5)
        RoundedButton(frame_botones_carrito, "✅ FINALIZAR VENTA", self.finalizar_venta,
                     '#2f855a', '#38a169', width=170, height=36).pack(side=tk.RIGHT, padx=5)

        self.cargar_lista_productos()

    def generar_ticket(self, total, productos_vendidos, subtotal_sin_iva, iva_calculado):
        """Ticket profesional usando un widget Text monoespaciado para alineación perfecta"""
        ticket_ventana = tk.Toplevel(self.root)
        ticket_ventana.title("🧾 Ticket de Venta")
        ticket_ventana.configure(bg='white')
        ticket_ventana.resizable(False, False)

        ancho = 520
        alto = 450
        ticket_ventana.geometry(f"{ancho}x{alto}")
        # Centrar
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (ancho // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (alto // 2)
        ticket_ventana.geometry(f"+{x}+{y}")
        ticket_ventana.transient(self.root)
        ticket_ventana.grab_set()

        # Frame principal
        main = tk.Frame(ticket_ventana, bg='white')
        main.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        # Text widget con scroll
        texto_ticket = tk.Text(main, font=('Courier New', 9), bg='white', fg='black',
                               wrap=tk.NONE, relief=tk.FLAT, state=tk.DISABLED)
        scroll = tk.Scrollbar(main, orient=tk.VERTICAL, command=texto_ticket.yview)
        texto_ticket.configure(yscrollcommand=scroll.set)
        texto_ticket.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Construir contenido del ticket
        ahora = datetime.now().strftime("%d/%m/%Y  %I:%M:%S %p")
        lineas = []
        lineas.append("═" * 42)
        lineas.append("        LOS BUENA ONDA")
        lineas.append("     ¡Siempre buena onda!")
        lineas.append("═" * 42)
        lineas.append(f"  Fecha: {ahora}")
        lineas.append("─" * 42)
        lineas.append(f"{'PRODUCTO':<20} {'CANT':>4} {'P.UNIT':>8} {'SUBTOTAL':>10}")
        lineas.append("─" * 42)

        for item in productos_vendidos:
            nombre = item['nombre'][:20]
            linea = f"{nombre:<20} {item['cantidad']:>4} {item['precio']:>8.2f} {item['subtotal']:>10.2f}"
            lineas.append(linea)

        lineas.append("─" * 42)
        lineas.append(f"{'Subtotal:':>32} {subtotal_sin_iva:>10.2f}")
        lineas.append(f"{'IVA (' + str(self.iva_porcentaje) + '%):':>32} {iva_calculado:>10.2f}")
        lineas.append(f"{'TOTAL:':>32} {total:>10.2f}")
        lineas.append("═" * 42)
        lineas.append("     ¡Gracias por su compra!")
        lineas.append("       Vuelva pronto 😊")
        lineas.append("═" * 42)

        # Insertar líneas en el Text (habilitar escritura temporalmente)
        texto_ticket.configure(state=tk.NORMAL)
        texto_ticket.delete("1.0", tk.END)
        texto_ticket.insert("1.0", "\n".join(lineas))
        texto_ticket.configure(state=tk.DISABLED)

        # Botón cerrar
        RoundedButton(main, "Cerrar", ticket_ventana.destroy,
                     COLOR_BOTON_SECUNDARIO, HOVER_SECUNDARIO, width=100, height=32).pack(pady=10)

    # Métodos de carrito (sin cambios sustanciales, excepto que total_venta ahora es subtotal sin IVA)
    def cargar_lista_productos(self):
        self.lista_productos.delete(0, tk.END)
        self.cursor.execute("SELECT id, nombre, precio, stock FROM productos WHERE stock > 0 ORDER BY nombre")
        for p in self.cursor.fetchall():
            self.lista_productos.insert(tk.END, f"{p[0]} | {p[1]} - ${p[2]:.2f} (Stock: {p[3]})")

    def buscar_producto_venta(self):
        busq = self.buscar_venta_entry.get()
        self.lista_productos.delete(0, tk.END)
        if busq:
            self.cursor.execute("SELECT id,nombre,precio,stock FROM productos WHERE nombre LIKE ? AND stock>0 ORDER BY nombre",
                                (f"%{busq}%",))
        else:
            self.cursor.execute("SELECT id,nombre,precio,stock FROM productos WHERE stock>0 ORDER BY nombre")
        for p in self.cursor.fetchall():
            self.lista_productos.insert(tk.END, f"{p[0]} | {p[1]} - ${p[2]:.2f} (Stock: {p[3]})")

    def agregar_al_carrito(self):
        seleccion = self.lista_productos.curselection()
        if not seleccion:
            return
        texto = self.lista_productos.get(seleccion[0])
        id_prod = int(texto.split(" | ")[0])
        self.cursor.execute("SELECT id,nombre,precio,stock FROM productos WHERE id=?", (id_prod,))
        prod = self.cursor.fetchone()
        try:
            cant = int(self.cantidad_entry.get())
            if cant <= 0:
                raise ValueError
        except:
            messagebox.showerror("Error", "Ingrese una cantidad válida")
            return
        if cant > prod[3]:
            messagebox.showerror("Stock", f"Solo hay {prod[3]} unidades disponibles")
            return
        for item in self.carrito:
            if item['id'] == prod[0]:
                nueva_cant = item['cantidad'] + cant
                if nueva_cant > prod[3]:
                    messagebox.showerror("Stock", "No hay suficiente stock para esa cantidad")
                    return
                item['cantidad'] = nueva_cant
                item['subtotal'] = item['precio'] * item['cantidad']
                break
        else:
            self.carrito.append({
                'id': prod[0],
                'nombre': prod[1],
                'precio': prod[2],
                'cantidad': cant,
                'subtotal': prod[2] * cant
            })
        self.actualizar_carrito()
        self.cantidad_entry.delete(0, tk.END)
        self.cantidad_entry.insert(0, "1")
        messagebox.showinfo("Éxito", f"Agregado {cant} × {prod[1]}")

    def actualizar_carrito(self):
        for item in self.tabla_carrito.get_children():
            self.tabla_carrito.delete(item)
        self.total_venta = 0.0
        for item in self.carrito:
            self.tabla_carrito.insert("", tk.END, values=(
                item['nombre'],
                f"${item['precio']:.2f}",
                item['cantidad'],
                f"${item['subtotal']:.2f}"
            ))
            self.total_venta += item['subtotal']
        # Mostrar el subtotal (sin IVA) en la interfaz, porque el IVA se calcula al final
        self.total_label.config(text=f"${self.total_venta:,.2f}")

    def eliminar_del_carrito(self):
        sel = self.tabla_carrito.selection()
        if not sel:
            return
        idx = self.tabla_carrito.index(sel[0])
        self.carrito.pop(idx)
        self.actualizar_carrito()

    def vaciar_carrito(self):
        if self.carrito and messagebox.askyesno("Confirmar", "¿Vaciar todo el carrito?"):
            self.carrito = []
            self.actualizar_carrito()

    def finalizar_venta(self):
        if not self.carrito:
            messagebox.showwarning("Carrito vacío", "No hay productos en el carrito.")
            return
        subtotal_sin_iva = self.total_venta
        iva_calculado = subtotal_sin_iva * (self.iva_porcentaje / 100)
        total_con_iva = subtotal_sin_iva + iva_calculado

        if messagebox.askyesno("Confirmar venta",
                               f"Subtotal: ${subtotal_sin_iva:,.2f}\n"
                               f"IVA ({self.iva_porcentaje}%): ${iva_calculado:,.2f}\n"
                               f"Total a cobrar: ${total_con_iva:,.2f}\n\n¿Confirma la venta?"):
            for item in self.carrito:
                self.cursor.execute("UPDATE productos SET stock = stock - ? WHERE id = ?",
                                    (item['cantidad'], item['id']))
            fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # Guardamos el total CON IVA
            self.cursor.execute("INSERT INTO ventas (fecha, total) VALUES (?, ?)", (fecha, total_con_iva))
            venta_id = self.cursor.lastrowid
            for item in self.carrito:
                self.cursor.execute('''INSERT INTO detalles_venta 
                                    (venta_id, producto_id, nombre, precio, cantidad, subtotal)
                                    VALUES (?,?,?,?,?,?)''',
                                    (venta_id, item['id'], item['nombre'], item['precio'],
                                     item['cantidad'], item['subtotal']))
            self.conn.commit()
            self.generar_ticket(total_con_iva, self.carrito.copy(), subtotal_sin_iva, iva_calculado)
            messagebox.showinfo("Venta completada", "La venta se registró exitosamente.\nSe ha generado el ticket.")
            self.carrito = []
            self.actualizar_carrito()
            self.mostrar_productos()
            self.cargar_lista_productos()
            self.buscar_venta_entry.delete(0, tk.END)
            self.buscar_producto_venta()

    # ===================== REPORTES (sin cambios) =====================
    def construir_reportes(self):
        main_frame = tk.Frame(self.frame_reportes, bg=COLOR_FONDO)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=25, pady=25)

        panel_izq = tk.Frame(main_frame, bg='white', relief=tk.RAISED, bd=2, width=200)
        panel_izq.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 12))
        panel_izq.pack_propagate(False)

        tk.Label(panel_izq, text="Reportes", font=('Segoe UI', 13, 'bold'),
                 bg='white', fg=COLOR_ENCABEZADO).pack(pady=15)

        RoundedButton(panel_izq, "📅 Ventas del mes", lambda: self.mostrar_reporte("ventas_mes"),
                     COLOR_BOTON_VENTA, HOVER_VENTA, width=160, height=40).pack(pady=6)
        RoundedButton(panel_izq, "🏆 Más vendido", lambda: self.mostrar_reporte("mas_vendido"),
                     COLOR_BOTON_MODIFICAR, HOVER_MODIFICAR, width=160, height=40).pack(pady=6)
        RoundedButton(panel_izq, "⚠️ Stock bajo", lambda: self.mostrar_reporte("stock_bajo"),
                     COLOR_BOTON_BUSCAR, HOVER_BUSCAR, width=160, height=40).pack(pady=6)
        RoundedButton(panel_izq, "📊 Resumen general", lambda: self.mostrar_reporte("resumen"),
                     COLOR_BOTON_REPORTE, HOVER_REPORTE, width=160, height=40).pack(pady=6)

        self.panel_derecho_reporte = tk.Frame(main_frame, bg='white', relief=tk.RAISED, bd=2)
        self.panel_derecho_reporte.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.reporte_tree = ttk.Treeview(self.panel_derecho_reporte, show='headings')
        self.reporte_tree.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)
        scroll_reporte = ttk.Scrollbar(self.panel_derecho_reporte, orient=tk.VERTICAL,
                                       command=self.reporte_tree.yview)
        self.reporte_tree.configure(yscrollcommand=scroll_reporte.set)
        scroll_reporte.pack(side=tk.RIGHT, fill=tk.Y)

        self.label_reporte_total = tk.Label(self.panel_derecho_reporte, text="",
                                            font=('Segoe UI', 10, 'bold'),
                                            bg='white', fg=COLOR_ENCABEZADO)
        self.label_reporte_total.pack(pady=8)

        self.mostrar_reporte("resumen")

    def mostrar_reporte(self, tipo):
        for item in self.reporte_tree.get_children():
            self.reporte_tree.delete(item)
        self.label_reporte_total.config(text="")

        if tipo == "ventas_mes":
            self.reporte_tree["columns"] = ("ID Venta", "Fecha", "Total")
            self.reporte_tree.heading("ID Venta", text="ID")
            self.reporte_tree.heading("Fecha", text="Fecha")
            self.reporte_tree.heading("Total", text="Total ($)")
            self.reporte_tree.column("ID Venta", width=70, anchor='center')
            self.reporte_tree.column("Fecha", width=220)
            self.reporte_tree.column("Total", width=130, anchor='center')
            hoy = datetime.now()
            mes_actual = hoy.strftime("%Y-%m")
            self.cursor.execute("SELECT id, fecha, total FROM ventas WHERE fecha LIKE ? ORDER BY id",
                                (f"{mes_actual}%",))
            ventas = self.cursor.fetchall()
            total_mes = sum(v[2] for v in ventas)
            for v in ventas:
                self.reporte_tree.insert("", tk.END, values=v)
            self.label_reporte_total.config(text=f"💰 Total ventas del mes: ${total_mes:,.2f}")

        elif tipo == "mas_vendido":
            self.reporte_tree["columns"] = ("Producto", "Cantidad vendida")
            self.reporte_tree.heading("Producto", text="Producto")
            self.reporte_tree.heading("Cantidad vendida", text="Unidades vendidas")
            self.reporte_tree.column("Producto", width=320)
            self.reporte_tree.column("Cantidad vendida", width=130, anchor='center')
            self.cursor.execute('''SELECT nombre, SUM(cantidad) as total_vendido 
                                   FROM detalles_venta 
                                   GROUP BY producto_id 
                                   ORDER BY total_vendido DESC 
                                   LIMIT 10''')
            productos = self.cursor.fetchall()
            for p in productos:
                self.reporte_tree.insert("", tk.END, values=p)
            if productos:
                self.label_reporte_total.config(text=f"🏆 Producto estrella: {productos[0][0]} ({productos[0][1]} uds.)")

        elif tipo == "stock_bajo":
            self.reporte_tree["columns"] = ("ID", "Producto", "Precio", "Stock")
            self.reporte_tree.heading("ID", text="ID")
            self.reporte_tree.heading("Producto", text="Producto")
            self.reporte_tree.heading("Precio", text="Precio ($)")
            self.reporte_tree.heading("Stock", text="Stock")
            self.reporte_tree.column("ID", width=60, anchor='center')
            self.reporte_tree.column("Producto", width=280)
            self.reporte_tree.column("Precio", width=110, anchor='center')
            self.reporte_tree.column("Stock", width=80, anchor='center')
            self.cursor.execute("SELECT id, nombre, precio, stock FROM productos WHERE stock < 5 AND stock > 0 ORDER BY stock")
            prods = self.cursor.fetchall()
            for p in prods:
                self.reporte_tree.insert("", tk.END, values=p)
            self.label_reporte_total.config(text=f"⚠️ Productos con stock bajo: {len(prods)}")

        elif tipo == "resumen":
            self.reporte_tree["columns"] = ("Indicador", "Valor")
            self.reporte_tree.heading("Indicador", text="Indicador")
            self.reporte_tree.heading("Valor", text="Valor")
            self.reporte_tree.column("Indicador", width=270)
            self.reporte_tree.column("Valor", width=150, anchor='center')
            self.cursor.execute("SELECT COUNT(*) FROM productos")
            total_prod = self.cursor.fetchone()[0]
            self.cursor.execute("SELECT COUNT(*) FROM ventas")
            total_ventas = self.cursor.fetchone()[0]
            self.cursor.execute("SELECT SUM(total) FROM ventas")
            ingreso = self.cursor.fetchone()[0] or 0
            self.cursor.execute("SELECT SUM(stock) FROM productos")
            stock_total = self.cursor.fetchone()[0] or 0
            datos = [
                ("📦 Total productos registrados", total_prod),
                ("🛒 Total ventas realizadas", total_ventas),
                ("💰 Ingresos totales", f"${ingreso:,.2f}"),
                ("📊 Stock total en inventario", stock_total)
            ]
            for d in datos:
                self.reporte_tree.insert("", tk.END, values=d)
            self.label_reporte_total.config(text="📋 Resumen general del negocio")

    # ========== GESTIÓN DE PRODUCTOS (igual, con validaciones) ==========
    def mostrar_productos(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.cursor.execute("SELECT * FROM productos ORDER BY id")
        productos = self.cursor.fetchall()
        for p in productos:
            self.tree.insert("", tk.END, values=p)
        self.label_total.config(text=f"Total de productos: {len(productos)}")
        self.precio_min_entry.delete(0, tk.END)
        self.precio_max_entry.delete(0, tk.END)

    def seleccionar_producto(self, event):
        sel = self.tree.selection()
        if sel:
            vals = self.tree.item(sel[0], "values")
            self.nombre_entry.delete(0, tk.END)
            self.nombre_entry.insert(0, vals[1])
            self.precio_entry.delete(0, tk.END)
            self.precio_entry.insert(0, vals[2])
            self.stock_entry.delete(0, tk.END)
            self.stock_entry.insert(0, vals[3])

    def agregar_producto(self):
        nombre = self.nombre_entry.get().strip()
        precio = self.precio_entry.get().strip()
        stock = self.stock_entry.get().strip()
        if not nombre or not precio or not stock:
            messagebox.showwarning("Campos incompletos", "Complete todos los campos.")
            return
        try:
            precio = float(precio)
            stock = int(stock)
            if precio < 0 or stock < 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Precio y stock deben ser números positivos.")
            return
        self.cursor.execute("INSERT INTO productos (nombre, precio, stock) VALUES (?,?,?)",
                            (nombre, precio, stock))
        self.conn.commit()
        self.mostrar_productos()
        self.limpiar_campos()
        self.cargar_lista_productos()
        messagebox.showinfo("Éxito", "Producto agregado correctamente.")

    def modificar_producto(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Selección requerida", "Seleccione un producto de la tabla.")
            return
        id_prod = self.tree.item(sel[0], "values")[0]
        nombre = self.nombre_entry.get().strip()
        precio = self.precio_entry.get().strip()
        stock = self.stock_entry.get().strip()
        if not nombre or not precio or not stock:
            messagebox.showwarning("Campos incompletos", "Complete todos los campos.")
            return
        try:
            precio = float(precio)
            stock = int(stock)
            if precio < 0 or stock < 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Precio y stock deben ser números positivos.")
            return
        self.cursor.execute("UPDATE productos SET nombre=?, precio=?, stock=? WHERE id=?",
                            (nombre, precio, stock, id_prod))
        self.conn.commit()
        self.mostrar_productos()
        self.limpiar_campos()
        self.cargar_lista_productos()
        messagebox.showinfo("Éxito", "Producto modificado correctamente.")

    def buscar_producto(self):
        nombre = self.nombre_entry.get().strip()
        if not nombre:
            messagebox.showwarning("Búsqueda", "Ingrese un nombre para buscar.")
            return
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.cursor.execute("SELECT * FROM productos WHERE nombre LIKE ?", (f"%{nombre}%",))
        productos = self.cursor.fetchall()
        for p in productos:
            self.tree.insert("", tk.END, values=p)
        self.label_total.config(text=f"Productos encontrados: {len(productos)}")
        if not productos:
            messagebox.showinfo("Búsqueda", "No se encontraron productos con ese nombre.")

    def eliminar_producto(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Selección requerida", "Seleccione un producto de la tabla.")
            return
        if messagebox.askyesno("Confirmar eliminación", "¿Está seguro de eliminar este producto?"):
            id_prod = self.tree.item(sel[0], "values")[0]
            self.cursor.execute("DELETE FROM productos WHERE id=?", (id_prod,))
            self.conn.commit()
            self.mostrar_productos()
            self.limpiar_campos()
            self.cargar_lista_productos()
            messagebox.showinfo("Eliminado", "Producto eliminado correctamente.")

    def limpiar_campos(self):
        self.nombre_entry.delete(0, tk.END)
        self.precio_entry.delete(0, tk.END)
        self.stock_entry.delete(0, tk.END)

# ===================== INICIO DE LA APLICACIÓN =====================
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    if not login():
        root.destroy()
        sys.exit(0)
    root.deiconify()
    app = SistemaPOS(root)
    root.mainloop()
