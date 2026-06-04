import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime
import os

# Colores profesionales (paleta sobria)
COLOR_FONDO = "#f4f6f9"          # Gris muy claro
COLOR_ENCABEZADO = "#1e3a5f"     # Azul marino profundo
COLOR_BOTON_AGREGAR = "#2c6e2f"  # Verde oscuro
COLOR_BOTON_MODIFICAR = "#2c5282" # Azul medio
COLOR_BOTON_ELIMINAR = "#9b2c2c" # Rojo ladrillo
COLOR_BOTON_BUSCAR = "#b45f06"   # Naranja quemado
COLOR_BOTON_VENTA = "#2b6a9e"    # Azul cielo
COLOR_TOTAL = "#23166d"          # Verde musgo
COLOR_BOTON_SECUNDARIO = "#4a5568" # Gris pizarra

class SistemaPOS:
    def __init__(self, root):
        self.root = root
        self.root.title("Tienda Unidos - Punto de Venta")
        self.root.geometry("1300x750")
        self.root.configure(bg=COLOR_FONDO)
        
        # Variables
        self.carrito = []
        self.total_venta = 0.0
        
        # Base de datos
        self.conn = sqlite3.connect('tienda_unidos.db')
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
        
        # Crear interfaz
        self.crear_interfaz()
        self.mostrar_productos()
        self.actualizar_reloj()
    
    def actualizar_reloj(self):
        ahora = datetime.now()
        fecha_hora = ahora.strftime("%d/%m/%Y  |  %I:%M:%S %p")
        self.reloj_label.config(text=f"📅 {fecha_hora}")
        self.root.after(1000, self.actualizar_reloj)
    
    def crear_interfaz(self):
        # Frame superior
        frame_superior = tk.Frame(self.root, bg=COLOR_ENCABEZADO, height=80)
        frame_superior.pack(fill=tk.X)
        
        titulo = tk.Label(frame_superior, text="TIENDA UNIDOS", 
                         font=('Segoe UI', 24, 'bold'), bg=COLOR_ENCABEZADO, fg='white')
        titulo.pack(side=tk.LEFT, padx=20, pady=15)
        
        self.reloj_label = tk.Label(frame_superior, text="", font=('Segoe UI', 12, 'bold'),
                                    bg=COLOR_ENCABEZADO, fg='#ecc94b')
        self.reloj_label.pack(side=tk.RIGHT, padx=20, pady=15)
        
        subtitulo = tk.Label(self.root, text="Sistema de inventario y ventas", 
                            font=('Segoe UI', 12), bg=COLOR_ENCABEZADO, fg='#cbd5e0')
        subtitulo.pack(fill=tk.X)
        
        # Notebook (pestañas)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.frame_productos = ttk.Frame(self.notebook)
        self.frame_ventas = ttk.Frame(self.notebook)
        self.frame_reportes = ttk.Frame(self.notebook)  # Nueva pestaña de reportes
        self.notebook.add(self.frame_productos, text="📦 INVENTARIO")
        self.notebook.add(self.frame_ventas, text="💰 PUNTO DE VENTA")
        self.notebook.add(self.frame_reportes, text="📊 REPORTES")
        
        self.construir_productos()
        self.construir_ventas()
        self.construir_reportes()
    
    def construir_productos(self):
        main_frame = tk.Frame(self.frame_productos, bg=COLOR_FONDO)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        titulo = tk.Label(main_frame, text="Administración de Productos", 
                         font=('Segoe UI', 16, 'bold'), bg=COLOR_FONDO, fg=COLOR_ENCABEZADO)
        titulo.pack(anchor=tk.W, pady=(0, 15))
        
        # Panel de búsqueda avanzada (por rango de precios)
        frame_busqueda_avanzada = tk.Frame(main_frame, bg='white', relief=tk.RAISED, bd=1)
        frame_busqueda_avanzada.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(frame_busqueda_avanzada, text="Buscar por rango de precio:", font=('Segoe UI', 10, 'bold'), bg='white').pack(side=tk.LEFT, padx=10, pady=5)
        tk.Label(frame_busqueda_avanzada, text="Min:", bg='white').pack(side=tk.LEFT, padx=(10,2))
        self.precio_min_entry = tk.Entry(frame_busqueda_avanzada, width=8, font=('Segoe UI', 10))
        self.precio_min_entry.pack(side=tk.LEFT, padx=2)
        tk.Label(frame_busqueda_avanzada, text="Max:", bg='white').pack(side=tk.LEFT, padx=2)
        self.precio_max_entry = tk.Entry(frame_busqueda_avanzada, width=8, font=('Segoe UI', 10))
        self.precio_max_entry.pack(side=tk.LEFT, padx=2)
        btn_filtrar = tk.Button(frame_busqueda_avanzada, text="🔍 Filtrar", command=self.buscar_productos_por_precio,
                               bg=COLOR_BOTON_BUSCAR, fg='white', relief=tk.FLAT, padx=10)
        btn_filtrar.pack(side=tk.LEFT, padx=10)
        btn_mostrar_todos = tk.Button(frame_busqueda_avanzada, text="🔄 Mostrar todos", command=self.mostrar_productos,
                                    bg=COLOR_BOTON_SECUNDARIO, fg='white', relief=tk.FLAT, padx=10)
        btn_mostrar_todos.pack(side=tk.LEFT, padx=5)
        
        # Frame de entrada de datos (tarjeta)
        card_frame = tk.Frame(main_frame, bg='white', relief=tk.RAISED, bd=1)
        card_frame.pack(fill=tk.X, pady=(0, 20))
        
        tk.Label(card_frame, text="Nombre:", font=('Segoe UI', 10, 'bold'), bg='white').grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
        self.nombre_entry = tk.Entry(card_frame, font=('Segoe UI', 11), width=30, bg='#fafafa', relief=tk.FLAT, bd=1)
        self.nombre_entry.grid(row=0, column=1, padx=10, pady=10)
        
        tk.Label(card_frame, text="Precio ($):", font=('Segoe UI', 10, 'bold'), bg='white').grid(row=0, column=2, padx=10, pady=10, sticky=tk.W)
        self.precio_entry = tk.Entry(card_frame, font=('Segoe UI', 11), width=15, bg='#fafafa', relief=tk.FLAT, bd=1)
        self.precio_entry.grid(row=0, column=3, padx=10, pady=10)
        
        tk.Label(card_frame, text="Stock:", font=('Segoe UI', 10, 'bold'), bg='white').grid(row=0, column=4, padx=10, pady=10, sticky=tk.W)
        self.stock_entry = tk.Entry(card_frame, font=('Segoe UI', 11), width=15, bg='#fafafa', relief=tk.FLAT, bd=1)
        self.stock_entry.grid(row=0, column=5, padx=10, pady=10)
        
        # Botones con colores profesionales
        botones = [
            ("➕ AGREGAR", self.agregar_producto, COLOR_BOTON_AGREGAR),
            ("✏️ MODIFICAR", self.modificar_producto, COLOR_BOTON_MODIFICAR),
            ("🔍 BUSCAR", self.buscar_producto, COLOR_BOTON_BUSCAR),
            ("🗑️ ELIMINAR", self.eliminar_producto, COLOR_BOTON_ELIMINAR),
            ("🔄 ACTUALIZAR", self.mostrar_productos, COLOR_BOTON_SECUNDARIO),
            ("📈 ESTADÍSTICAS", self.mostrar_estadisticas, COLOR_BOTON_VENTA),
            ("📎 EXPORTAR EXCEL", self.exportar_productos_excel, COLOR_BOTON_SECUNDARIO)
        ]
        for i, (text, comando, color) in enumerate(botones):
            btn = tk.Button(card_frame, text=text, command=comando, bg=color, fg='white',
                           font=('Segoe UI', 10, 'bold'), relief=tk.FLAT, padx=10, pady=5, cursor='hand2')
            btn.grid(row=1, column=i, padx=5, pady=10)
        
        # Tabla de productos
        tabla_frame = tk.Frame(main_frame, bg='white')
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
        self.tree.column("ID", width=60, anchor='center')
        self.tree.column("Nombre", width=400)
        self.tree.column("Precio", width=120, anchor='center')
        self.tree.column("Stock", width=100, anchor='center')
        
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scroll_y.grid(row=0, column=1, sticky=(tk.N, tk.S))
        scroll_x.grid(row=1, column=0, sticky=(tk.W, tk.E))
        tabla_frame.columnconfigure(0, weight=1)
        tabla_frame.rowconfigure(0, weight=1)
        
        self.tree.bind('<<TreeviewSelect>>', self.seleccionar_producto)
        self.label_total = tk.Label(main_frame, text="Total de productos: 0", font=('Segoe UI', 10, 'italic'),
                                    bg=COLOR_FONDO, fg='#4a5568')
        self.label_total.pack(anchor=tk.W, pady=(10, 0))
    
    def buscar_productos_por_precio(self):
        """Filtra productos por rango de precio"""
        try:
            min_precio = float(self.precio_min_entry.get()) if self.precio_min_entry.get() else 0
            max_precio = float(self.precio_max_entry.get()) if self.precio_max_entry.get() else float('inf')
        except ValueError:
            messagebox.showerror("Error", "Ingrese valores numéricos válidos para el rango de precios.")
            return
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.cursor.execute("SELECT * FROM productos WHERE precio BETWEEN ? AND ? ORDER BY id", (min_precio, max_precio))
        productos = self.cursor.fetchall()
        for producto in productos:
            self.tree.insert("", tk.END, values=producto)
        self.label_total.config(text=f"Productos encontrados: {len(productos)}")
        if not productos:
            messagebox.showinfo("Búsqueda", "No hay productos en ese rango de precios.")
    
    def mostrar_estadisticas(self):
        """Ventana con estadísticas: ventas totales y productos con stock bajo"""
        self.cursor.execute("SELECT SUM(total) FROM ventas")
        ventas_totales = self.cursor.fetchone()[0] or 0
        self.cursor.execute("SELECT COUNT(*) FROM productos WHERE stock < 5 AND stock > 0")
        stock_bajo = self.cursor.fetchone()[0]
        stats = f"💰 Ventas totales acumuladas: ${ventas_totales:.2f}\n⚠️ Productos con stock bajo (<5 unidades): {stock_bajo}"
        messagebox.showinfo("Estadísticas del negocio", stats)
    
    def exportar_productos_excel(self):
        """Exporta la lista de productos a un archivo Excel"""
        try:
            import openpyxl
            from openpyxl.styles import Font, Alignment
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Productos"
            # Encabezados
            headers = ["ID", "Nombre", "Precio", "Stock"]
            for col, header in enumerate(headers, 1):
                cell = ws.cell(row=1, column=col, value=header)
                cell.font = Font(bold=True)
                cell.alignment = Alignment(horizontal="center")
            # Datos
            self.cursor.execute("SELECT id, nombre, precio, stock FROM productos ORDER BY id")
            for row, prod in enumerate(self.cursor.fetchall(), 2):
                ws.cell(row=row, column=1, value=prod[0])
                ws.cell(row=row, column=2, value=prod[1])
                ws.cell(row=row, column=3, value=prod[2])
                ws.cell(row=row, column=4, value=prod[3])
            for col in range(1, 5):
                ws.column_dimensions[chr(64+col)].width = 15
            wb.save("productos_exportados.xlsx")
            messagebox.showinfo("Exportar", "Productos exportados a 'productos_exportados.xlsx'")
        except ImportError:
            messagebox.showerror("Error", "No se encontró la librería openpyxl. Instálela con: pip install openpyxl")
    
    # El resto de métodos (construir_ventas, generar_ticket, etc.) se mantienen pero con ligeros ajustes de color
    # Para no hacer más extenso el código, mantendré las funciones originales actualizadas con los nuevos colores y corrección del ticket.
    # (A continuación se incluyen los métodos de ventas y ticket mejorados. Como el código es muy largo, los pondré con la misma lógica pero ajustando colores y posición del ticket.)
    
    def construir_ventas(self):
        # Ídem a tu código original, solo cambiando colores a los profesionales
        main_frame = tk.Frame(self.frame_ventas, bg=COLOR_FONDO)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        panel_izq = tk.Frame(main_frame, bg=COLOR_FONDO)
        panel_izq.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        panel_der = tk.Frame(main_frame, bg=COLOR_FONDO)
        panel_der.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))
        
        # Card izquierda
        card_izq = tk.Frame(panel_izq, bg='white', relief=tk.RAISED, bd=1)
        card_izq.pack(fill=tk.BOTH, expand=True)
        tk.Label(card_izq, text="🛒 SELECCIONAR PRODUCTO", font=('Segoe UI', 14, 'bold'),
                 bg=COLOR_ENCABEZADO, fg='white', pady=10).pack(fill=tk.X)
        
        frame_buscar = tk.Frame(card_izq, bg='white', pady=10)
        frame_buscar.pack(fill=tk.X, padx=15, pady=10)
        tk.Label(frame_buscar, text="Buscar:", font=('Segoe UI', 10, 'bold'), bg='white').pack(side=tk.LEFT)
        self.buscar_venta_entry = tk.Entry(frame_buscar, font=('Segoe UI', 11), width=40)
        self.buscar_venta_entry.pack(side=tk.LEFT, padx=10)
        tk.Button(frame_buscar, text="🔍", command=self.buscar_producto_venta,
                  bg=COLOR_BOTON_BUSCAR, fg='white', relief=tk.FLAT, padx=15).pack(side=tk.LEFT)
        
        tk.Label(card_izq, text="Productos disponibles:", font=('Segoe UI', 10, 'bold'), bg='white').pack(anchor=tk.W, padx=15)
        frame_lista = tk.Frame(card_izq, bg='white')
        frame_lista.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        scroll_lista = tk.Scrollbar(frame_lista)
        self.lista_productos = tk.Listbox(frame_lista, height=12, font=('Segoe UI', 10),
                                          yscrollcommand=scroll_lista.set, bg='#fafafa')
        scroll_lista.config(command=self.lista_productos.yview)
        self.lista_productos.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll_lista.pack(side=tk.RIGHT, fill=tk.Y)
        
        frame_cantidad = tk.Frame(card_izq, bg='white', pady=10)
        frame_cantidad.pack(fill=tk.X, padx=15, pady=10)
        tk.Label(frame_cantidad, text="Cantidad:", font=('Segoe UI', 10, 'bold'), bg='white').pack(side=tk.LEFT)
        self.cantidad_entry = tk.Entry(frame_cantidad, width=10, font=('Segoe UI', 11))
        self.cantidad_entry.pack(side=tk.LEFT, padx=10)
        self.cantidad_entry.insert(0, "1")
        tk.Button(frame_cantidad, text="➕ AGREGAR AL CARRITO", command=self.agregar_al_carrito,
                  bg=COLOR_BOTON_AGREGAR, fg='white', font=('Segoe UI', 10, 'bold'),
                  relief=tk.FLAT, padx=20, pady=5).pack(side=tk.LEFT, padx=10)
        
        # Card derecha (carrito)
        card_der = tk.Frame(panel_der, bg='white', relief=tk.RAISED, bd=1)
        card_der.pack(fill=tk.BOTH, expand=True)
        tk.Label(card_der, text="🛍️ CARRITO DE COMPRAS", font=('Segoe UI', 14, 'bold'),
                 bg=COLOR_ENCABEZADO, fg='white', pady=10).pack(fill=tk.X)
        
        frame_tabla_carrito = tk.Frame(card_der, bg='white')
        frame_tabla_carrito.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        scroll_carrito_y = ttk.Scrollbar(frame_tabla_carrito, orient=tk.VERTICAL)
        scroll_carrito_x = ttk.Scrollbar(frame_tabla_carrito, orient=tk.HORIZONTAL)
        self.tabla_carrito = ttk.Treeview(frame_tabla_carrito,
                                          columns=("Producto", "Precio", "Cantidad", "Subtotal"),
                                          show="headings", height=8,
                                          yscrollcommand=scroll_carrito_y.set,
                                          xscrollcommand=scroll_carrito_x.set)
        self.tabla_carrito.heading("Producto", text="PRODUCTO")
        self.tabla_carrito.heading("Precio", text="PRECIO ($)")
        self.tabla_carrito.heading("Cantidad", text="CANTIDAD")
        self.tabla_carrito.heading("Subtotal", text="SUBTOTAL ($)")
        for col in ("Producto", "Precio", "Cantidad", "Subtotal"):
            self.tabla_carrito.column(col, width=150 if col=="Producto" else 80, anchor='center')
        self.tabla_carrito.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scroll_carrito_y.grid(row=0, column=1, sticky=(tk.N, tk.S))
        scroll_carrito_x.grid(row=1, column=0, sticky=(tk.W, tk.E))
        frame_tabla_carrito.columnconfigure(0, weight=1)
        frame_tabla_carrito.rowconfigure(0, weight=1)
        
        frame_total = tk.Frame(card_der, bg=COLOR_TOTAL, pady=15)
        frame_total.pack(fill=tk.X, padx=15, pady=10)
        tk.Label(frame_total, text="TOTAL:", font=('Segoe UI', 18, 'bold'), bg=COLOR_TOTAL, fg='white').pack(side=tk.LEFT, padx=20)
        self.total_label = tk.Label(frame_total, text="$0.00", font=('Segoe UI', 24, 'bold'),
                                    bg=COLOR_TOTAL, fg='#fbd38d')
        self.total_label.pack(side=tk.RIGHT, padx=20)
        
        frame_botones_carrito = tk.Frame(card_der, bg='white')
        frame_botones_carrito.pack(fill=tk.X, padx=15, pady=10)
        tk.Button(frame_botones_carrito, text="🗑️ ELIMINAR SELECCIONADO", command=self.eliminar_del_carrito,
                  bg=COLOR_BOTON_ELIMINAR, fg='white', font=('Segoe UI', 10),
                  relief=tk.FLAT, padx=10).pack(side=tk.LEFT, padx=5)
        tk.Button(frame_botones_carrito, text="🔄 VACIAR CARRITO", command=self.vaciar_carrito,
                  bg=COLOR_BOTON_SECUNDARIO, fg='white', font=('Segoe UI', 10),
                  relief=tk.FLAT, padx=10).pack(side=tk.LEFT, padx=5)
        tk.Button(frame_botones_carrito, text="✅ FINALIZAR VENTA", command=self.finalizar_venta,
                  bg='#2c6e2f', fg='white', font=('Segoe UI', 10, 'bold'),
                  relief=tk.FLAT, padx=20, pady=5).pack(side=tk.RIGHT, padx=5)
        
        self.cargar_lista_productos()
    
    def generar_ticket(self, venta_id, total, productos_vendidos):
        """Ventana de ticket centrada y bien presentada"""
        ticket_ventana = tk.Toplevel(self.root)
        ticket_ventana.title("🧾 Ticket de Venta")
        ticket_ventana.geometry("450x550")
        ticket_ventana.configure(bg='white')
        ticket_ventana.resizable(False, False)
        # Centrar respecto a la ventana principal
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - 225
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - 275
        ticket_ventana.geometry(f"+{x}+{y}")
        ticket_ventana.transient(self.root)
        ticket_ventana.grab_set()
        
        frame_ticket = tk.Frame(ticket_ventana, bg='white', padx=20, pady=20)
        frame_ticket.pack(fill=tk.BOTH, expand=True)
        
        # Contenido del ticket (igual que antes pero con tipografía Courier para impresora)
        tk.Label(frame_ticket, text="="*40, bg='white', fg='black').pack()
        tk.Label(frame_ticket, text="         TIENDA UNIDOS", font=('Courier', 14, 'bold'), bg='white', fg='black').pack()
        tk.Label(frame_ticket, text="         ¡Tu mejor opción!", font=('Courier', 10), bg='white', fg='gray').pack()
        tk.Label(frame_ticket, text="="*40, bg='white', fg='black').pack()
        
        ahora = datetime.now().strftime("%d/%m/%Y %I:%M:%S %p")
        tk.Label(frame_ticket, text=f"Fecha: {ahora}", font=('Courier', 9), bg='white', fg='black').pack(anchor=tk.W, pady=(10,0))
        tk.Label(frame_ticket, text=f"Venta #: {venta_id}", font=('Courier', 9, 'bold'), bg='white', fg='black').pack(anchor=tk.W)
        tk.Label(frame_ticket, text="- "*20, bg='white', fg='black').pack(pady=5)
        
        encabezado = tk.Frame(frame_ticket, bg='white')
        encabezado.pack(fill=tk.X)
        tk.Label(encabezado, text="Producto", font=('Courier', 9, 'bold'), bg='white', width=20, anchor=tk.W).pack(side=tk.LEFT)
        tk.Label(encabezado, text="Cant", font=('Courier', 9, 'bold'), bg='white', width=5, anchor=tk.CENTER).pack(side=tk.LEFT)
        tk.Label(encabezado, text="Subtotal", font=('Courier', 9, 'bold'), bg='white', width=10, anchor=tk.RIGHT).pack(side=tk.RIGHT)
        tk.Label(frame_ticket, text="- "*20, bg='white', fg='black').pack()
        
        for item in productos_vendidos:
            fila = tk.Frame(frame_ticket, bg='white')
            fila.pack(fill=tk.X)
            nombre_corto = item['nombre'][:20]
            tk.Label(fila, text=nombre_corto, font=('Courier', 9), bg='white', width=20, anchor=tk.W).pack(side=tk.LEFT)
            tk.Label(fila, text=str(item['cantidad']), font=('Courier', 9), bg='white', width=5, anchor=tk.CENTER).pack(side=tk.LEFT)
            tk.Label(fila, text=f"${item['subtotal']:.2f}", font=('Courier', 9), bg='white', width=10, anchor=tk.RIGHT).pack(side=tk.RIGHT)
        
        tk.Label(frame_ticket, text="- "*20, bg='white', fg='black').pack(pady=5)
        tk.Label(frame_ticket, text=f"TOTAL: ${total:.2f}", font=('Courier', 12, 'bold'), bg='white', fg='green').pack(anchor=tk.E)
        tk.Label(frame_ticket, text="="*40, bg='white', fg='black').pack(pady=10)
        tk.Label(frame_ticket, text="     ¡Gracias por su compra!", font=('Courier', 10), bg='white', fg='blue').pack()
        tk.Label(frame_ticket, text="     Vuelva pronto", font=('Courier', 9), bg='white', fg='gray').pack()
        tk.Label(frame_ticket, text="="*40, bg='white', fg='black').pack()
        
        tk.Button(frame_ticket, text="Cerrar", command=ticket_ventana.destroy,
                 bg=COLOR_BOTON_SECUNDARIO, fg='white', font=('Segoe UI', 10),
                 relief=tk.FLAT, padx=20, pady=5, cursor='hand2').pack(pady=15)
    
    # ========== MÉTODOS DE VENTAS (sin cambios sustanciales, solo asegurar que llamen a generar_ticket correctamente) ==========
    def cargar_lista_productos(self):
        self.lista_productos.delete(0, tk.END)
        self.cursor.execute("SELECT id, nombre, precio, stock FROM productos WHERE stock > 0 ORDER BY nombre")
        for p in self.cursor.fetchall():
            self.lista_productos.insert(tk.END, f"{p[0]} | {p[1]} - ${p[2]:.2f} (Stock: {p[3]})")
    
    def buscar_producto_venta(self):
        busq = self.buscar_venta_entry.get()
        self.lista_productos.delete(0, tk.END)
        if busq:
            self.cursor.execute("SELECT id,nombre,precio,stock FROM productos WHERE nombre LIKE ? AND stock>0 ORDER BY nombre", (f"%{busq}%",))
        else:
            self.cursor.execute("SELECT id,nombre,precio,stock FROM productos WHERE stock>0 ORDER BY nombre")
        for p in self.cursor.fetchall():
            self.lista_productos.insert(tk.END, f"{p[0]} | {p[1]} - ${p[2]:.2f} (Stock: {p[3]})")
    
    def agregar_al_carrito(self):
        seleccion = self.lista_productos.curselection()
        if not seleccion: return
        texto = self.lista_productos.get(seleccion[0])
        id_prod = int(texto.split(" | ")[0])
        self.cursor.execute("SELECT id,nombre,precio,stock FROM productos WHERE id=?", (id_prod,))
        prod = self.cursor.fetchone()
        try:
            cant = int(self.cantidad_entry.get())
            if cant<=0: raise ValueError
        except:
            messagebox.showerror("Error","Cantidad válida")
            return
        if cant > prod[3]:
            messagebox.showerror("Stock", f"Solo hay {prod[3]} unidades")
            return
        for item in self.carrito:
            if item['id']==prod[0]:
                new_cant = item['cantidad']+cant
                if new_cant > prod[3]:
                    messagebox.showerror("Stock","No hay suficiente stock")
                    return
                item['cantidad'] = new_cant
                item['subtotal'] = item['precio']*item['cantidad']
                break
        else:
            self.carrito.append({'id':prod[0],'nombre':prod[1],'precio':prod[2],'cantidad':cant,'subtotal':prod[2]*cant})
        self.actualizar_carrito()
        self.cantidad_entry.delete(0,tk.END)
        self.cantidad_entry.insert(0,"1")
        messagebox.showinfo("Éxito", f"Agregado {cant} de {prod[1]}")
    
    def actualizar_carrito(self):
        for item in self.tabla_carrito.get_children():
            self.tabla_carrito.delete(item)
        self.total_venta=0.0
        for item in self.carrito:
            self.tabla_carrito.insert("",tk.END, values=(item['nombre'], f"${item['precio']:.2f}", item['cantidad'], f"${item['subtotal']:.2f}"))
            self.total_venta += item['subtotal']
        self.total_label.config(text=f"${self.total_venta:.2f}")
    
    def eliminar_del_carrito(self):
        sel = self.tabla_carrito.selection()
        if not sel: return
        idx = self.tabla_carrito.index(sel[0])
        self.carrito.pop(idx)
        self.actualizar_carrito()
    
    def vaciar_carrito(self):
        if self.carrito and messagebox.askyesno("Confirmar","¿Vaciar carrito?"):
            self.carrito=[]
            self.actualizar_carrito()
    
    def finalizar_venta(self):
        if not self.carrito:
            messagebox.showwarning("Carrito","No hay productos")
            return
        if messagebox.askyesno("Confirmar", f"Total: ${self.total_venta:.2f}\n¿Confirmar venta?"):
            for item in self.carrito:
                self.cursor.execute("UPDATE productos SET stock = stock - ? WHERE id = ?", (item['cantidad'], item['id']))
            fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.cursor.execute("INSERT INTO ventas (fecha, total) VALUES (?, ?)", (fecha, self.total_venta))
            venta_id = self.cursor.lastrowid
            for item in self.carrito:
                self.cursor.execute("INSERT INTO detalles_venta (venta_id, producto_id, nombre, precio, cantidad, subtotal) VALUES (?,?,?,?,?,?)",
                                   (venta_id, item['id'], item['nombre'], item['precio'], item['cantidad'], item['subtotal']))
            self.conn.commit()
            self.generar_ticket(venta_id, self.total_venta, self.carrito.copy())
            messagebox.showinfo("Venta", f"Venta #{venta_id} completada\nTotal: ${self.total_venta:.2f}\nTicket generado.")
            self.carrito=[]
            self.actualizar_carrito()
            self.mostrar_productos()
            self.cargar_lista_productos()
            self.buscar_venta_entry.delete(0,tk.END)
            self.buscar_producto_venta()
    
    # ========== PESTAÑA DE REPORTES (nueva) ==========
    def construir_reportes(self):
        frame = tk.Frame(self.frame_reportes, bg=COLOR_FONDO)
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        tk.Label(frame, text="Reportes y Análisis", font=('Segoe UI', 16, 'bold'), bg=COLOR_FONDO, fg=COLOR_ENCABEZADO).pack(anchor=tk.W, pady=(0,20))
        
        # Botones de reportes rápidos
        btn_ventas_mes = tk.Button(frame, text="📅 Ventas del mes actual", command=self.reporte_ventas_mes,
                                  bg=COLOR_BOTON_VENTA, fg='white', font=('Segoe UI', 11), relief=tk.FLAT, padx=15, pady=10)
        btn_ventas_mes.pack(pady=5, anchor=tk.W)
        
        btn_prod_mas_vendido = tk.Button(frame, text="🏆 Producto más vendido", command=self.producto_mas_vendido,
                                        bg=COLOR_BOTON_MODIFICAR, fg='white', font=('Segoe UI', 11), relief=tk.FLAT, padx=15, pady=10)
        btn_prod_mas_vendido.pack(pady=5, anchor=tk.W)
        
        btn_stock_bajo = tk.Button(frame, text="⚠️ Productos con stock bajo", command=self.reporte_stock_bajo,
                                  bg=COLOR_BOTON_BUSCAR, fg='white', font=('Segoe UI', 11), relief=tk.FLAT, padx=15, pady=10)
        btn_stock_bajo.pack(pady=5, anchor=tk.W)
    
    def reporte_ventas_mes(self):
        """Muestra el total de ventas del mes actual"""
        hoy = datetime.now()
        mes_actual = hoy.strftime("%Y-%m")
        self.cursor.execute("SELECT SUM(total) FROM ventas WHERE fecha LIKE ?", (f"{mes_actual}%",))
        total_mes = self.cursor.fetchone()[0] or 0
        messagebox.showinfo("Ventas del mes", f"💰 Ventas acumuladas en {hoy.strftime('%B %Y')}: ${total_mes:.2f}")
    
    def producto_mas_vendido(self):
        """Producto con mayor cantidad vendida (suma de cantidades en detalles_venta)"""
        self.cursor.execute('''SELECT nombre, SUM(cantidad) as total_vendido FROM detalles_venta 
                               GROUP BY producto_id ORDER BY total_vendido DESC LIMIT 1''')
        res = self.cursor.fetchone()
        if res:
            messagebox.showinfo("Producto estrella", f"🏆 {res[0]} - {res[1]} unidades vendidas")
        else:
            messagebox.showinfo("Sin datos", "Aún no se han realizado ventas.")
    
    def reporte_stock_bajo(self):
        """Lista de productos con stock menor a 5"""
        self.cursor.execute("SELECT nombre, stock FROM productos WHERE stock < 5 AND stock > 0 ORDER BY stock")
        productos = self.cursor.fetchall()
        if productos:
            lista = "\n".join([f"{p[0]}: {p[1]} unidades" for p in productos])
            messagebox.showinfo("Stock bajo", f"Productos con menos de 5 unidades:\n\n{lista}")
        else:
            messagebox.showinfo("Stock bajo", "No hay productos con stock bajo.")
    
    # ========== MÉTODOS DE GESTIÓN DE PRODUCTOS (originales pero adaptados a nuevo color) ==========
    def mostrar_productos(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.cursor.execute("SELECT * FROM productos ORDER BY id")
        productos = self.cursor.fetchall()
        for p in productos:
            self.tree.insert("", tk.END, values=p)
        self.label_total.config(text=f"Total de productos: {len(productos)}")
        # Limpiar filtros de precio
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
        nombre = self.nombre_entry.get()
        precio = self.precio_entry.get()
        stock = self.stock_entry.get()
        if not nombre or not precio or not stock:
            messagebox.showwarning("Campos", "Complete todos los campos")
            return
        try:
            precio = float(precio)
            stock = int(stock)
            self.cursor.execute("INSERT INTO productos (nombre, precio, stock) VALUES (?,?,?)", (nombre,precio,stock))
            self.conn.commit()
            self.mostrar_productos()
            self.limpiar_campos()
            self.cargar_lista_productos()
            messagebox.showinfo("Éxito", "Producto agregado")
        except ValueError:
            messagebox.showerror("Error", "Precio debe ser número y stock entero")
    
    def modificar_producto(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Selección", "Seleccione un producto")
            return
        id_prod = self.tree.item(sel[0], "values")[0]
        nombre = self.nombre_entry.get()
        precio = self.precio_entry.get()
        stock = self.stock_entry.get()
        if not nombre or not precio or not stock:
            messagebox.showwarning("Campos", "Complete todos los campos")
            return
        try:
            precio = float(precio)
            stock = int(stock)
            self.cursor.execute("UPDATE productos SET nombre=?, precio=?, stock=? WHERE id=?", (nombre,precio,stock,id_prod))
            self.conn.commit()
            self.mostrar_productos()
            self.limpiar_campos()
            self.cargar_lista_productos()
            messagebox.showinfo("Éxito", "Producto modificado")
        except ValueError:
            messagebox.showerror("Error", "Datos inválidos")
    
    def buscar_producto(self):
        nombre = self.nombre_entry.get()
        if not nombre:
            messagebox.showwarning("Búsqueda", "Ingrese un nombre")
            return
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.cursor.execute("SELECT * FROM productos WHERE nombre LIKE ?", (f"%{nombre}%",))
        productos = self.cursor.fetchall()
        for p in productos:
            self.tree.insert("", tk.END, values=p)
        self.label_total.config(text=f"Productos encontrados: {len(productos)}")
        if not productos:
            messagebox.showinfo("Búsqueda", "No encontrado")
    
    def eliminar_producto(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Selección", "Seleccione un producto")
            return
        if messagebox.askyesno("Confirmar", "¿Eliminar producto?"):
            id_prod = self.tree.item(sel[0], "values")[0]
            self.cursor.execute("DELETE FROM productos WHERE id=?", (id_prod,))
            self.conn.commit()
            self.mostrar_productos()
            self.limpiar_campos()
            self.cargar_lista_productos()
            messagebox.showinfo("Éxito", "Producto eliminado")
    
    def limpiar_campos(self):
        self.nombre_entry.delete(0, tk.END)
        self.precio_entry.delete(0, tk.END)
        self.stock_entry.delete(0, tk.END)

if __name__ == "__main__":
    root = tk.Tk()
    app = SistemaPOS(root)
    root.mainloop()

