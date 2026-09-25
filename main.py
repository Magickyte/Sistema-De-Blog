
import customtkinter as ctk
from tkinter import messagebox
import oracledb

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

DB_CONFIG = {
    "user": "blog_user",
    "password": "contra",
    "dsn": "localhost/XEPDB1"
}

class AppBlog(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Sistema de Blog - Publicaciones, Categorías y Etiquetas")
        
        # Permitir redimensionar la ventana
        self.resizable(True, True)

        self.current_user_id = None
        self.current_user_name = ""
        self.current_user_role = "USER"

        self.dict_categories = {}
        self.dict_tags = {}
        self.cat_filter_dict = {"Todas las categorías": None}

        # Centrar la ventana al iniciar
        self.centrar_ventana(820, 900)

        self.pantalla_login()

    def centrar_ventana(self, ancho, alto):
        """Calcula la posición para centrar la ventana en la pantalla."""
        self.update_idletasks()
        pantalla_ancho = self.winfo_screenwidth()
        pantalla_alto = self.winfo_screenheight()

        pos_x = (pantalla_ancho // 2) - (ancho // 2)
        pos_y = (pantalla_alto // 2) - (alto // 2)

        if pos_y < 0:
            pos_y = 0

        self.geometry(f"{ancho}x{alto}+{pos_x}+{pos_y}")

    def conectar_db(self):
        return oracledb.connect(**DB_CONFIG)

    def limpiar_pantalla(self):
        for widget in self.winfo_children():
            widget.destroy()

    # -------------------------------------------------------------
    # PANTALLA: LOGIN
    # -------------------------------------------------------------
    def pantalla_login(self):
        self.limpiar_pantalla()

        frame = ctk.CTkFrame(self, width=380, height=350, corner_radius=15)
        frame.place(relx=0.5, rely=0.5, anchor="center")

        title = ctk.CTkLabel(frame, text="Acceso al Blog", font=("Roboto", 22, "bold"))
        title.pack(pady=(35, 20))

        self.ent_email = ctk.CTkEntry(frame, placeholder_text="Correo electrónico", width=280)
        self.ent_email.pack(pady=10)

        self.ent_password = ctk.CTkEntry(frame, placeholder_text="Contraseña", show="*", width=280)
        self.ent_password.pack(pady=10)

        btn_ingresar = ctk.CTkButton(frame, text="Ingresar", width=280, command=self.procesar_login)
        btn_ingresar.pack(pady=(20, 10))

    def procesar_login(self):
        email = self.ent_email.get().strip()
        password = self.ent_password.get().strip()

        if not email or not password:
            messagebox.showwarning("Atención", "Ingresa correo y contraseña.")
            return

        try:
            conn = self.conectar_db()
            cursor = conn.cursor()
            
            user_id_out = cursor.var(oracledb.NUMBER)
            name_out = cursor.var(oracledb.STRING)
            role_out = cursor.var(oracledb.STRING)
            
            cursor.callproc("sp_login", [email, password, user_id_out, name_out, role_out])
            
            self.current_user_id = int(user_id_out.getvalue())
            self.current_user_name = str(name_out.getvalue())
            self.current_user_role = str(role_out.getvalue())
            
            cursor.close()
            conn.close()

            self.pantalla_principal()

        except oracledb.DatabaseError as e:
            error_obj, = e.args
            if "ORA-20001" in error_obj.message:
                messagebox.showerror("Acceso Denegado", "Contraseña incorrecta.")
            elif "ORA-20002" in error_obj.message:
                messagebox.showerror("Acceso Denegado", "Usuario no registrado.")
            else:
                messagebox.showerror("Error de BD", f"{error_obj.message}")
        except Exception as e:
            messagebox.showerror("Error", f"Error de conexión: {e}")

    # -------------------------------------------------------------
    # PANTALLA PRINCIPAL
    # -------------------------------------------------------------
    def pantalla_principal(self):
        self.limpiar_pantalla()

        # Grid adaptable
        self.grid_rowconfigure(3, weight=1) # El Feed de posts se expande
        self.grid_columnconfigure(0, weight=1)

        # 1. Barra Superior (Fila 0)
        frame_top = ctk.CTkFrame(self, height=50, corner_radius=0)
        frame_top.grid(row=0, column=0, sticky="ew")

        badge_color = "#4CAF50" if self.current_user_role == "ADMIN" else "#2196F3"
        lbl_user = ctk.CTkLabel(frame_top, text=f"Usuario: {self.current_user_name} [{self.current_user_role}]", font=("Roboto", 14, "bold"), text_color=badge_color)
        lbl_user.pack(side="left", padx=20, pady=10)

        btn_logout = ctk.CTkButton(frame_top, text="Cerrar Sesión", fg_color="#E53935", hover_color="#C62828", width=110, command=self.cerrar_sesion)
        btn_logout.pack(side="right", padx=20, pady=10)

        # 2. Panel de Pestañas (Fila 1)
        tabview = ctk.CTkTabview(self, height=210)
        tabview.grid(row=1, column=0, padx=20, pady=5, sticky="ew")

        # Pestaña Publicar
        tab_pub = tabview.add("Publicar Artículo")
        
        self.ent_titulo = ctk.CTkEntry(tab_pub, placeholder_text="Título de la publicación...")
        self.ent_titulo.pack(fill="x", padx=10, pady=4)

        self.txt_texto = ctk.CTkTextbox(tab_pub, height=50)
        self.txt_texto.pack(fill="x", padx=10, pady=4)

        frame_cat_tag = ctk.CTkFrame(tab_pub, fg_color="transparent")
        frame_cat_tag.pack(fill="x", padx=10, pady=2)

        frame_cat = ctk.CTkFrame(frame_cat_tag)
        frame_cat.pack(side="left", fill="both", expand=True, padx=(0, 5))
        ctk.CTkLabel(frame_cat, text="Selecciona Categorías:", font=("Roboto", 11, "bold")).pack(anchor="w", padx=5, pady=2)

        frame_tag = ctk.CTkFrame(frame_cat_tag)
        frame_tag.pack(side="right", fill="both", expand=True, padx=(5, 0))
        ctk.CTkLabel(frame_tag, text="Selecciona Etiquetas / Tags:", font=("Roboto", 11, "bold")).pack(anchor="w", padx=5, pady=2)

        self.cargar_opciones_cat_tag(frame_cat, frame_tag)

        btn_guardar = ctk.CTkButton(tab_pub, text="Publicar", command=self.guardar_articulo)
        btn_guardar.pack(pady=5)

        # Pestañas para el ADMIN
        if self.current_user_role == "ADMIN":
            tab_user = tabview.add("Gestionar Usuarios")
            tab_categorias_admin = tabview.add("Categorías & Tags")

            # Sub-panel Usuarios
            self.ent_new_name = ctk.CTkEntry(tab_user, placeholder_text="Nombre completo", width=180)
            self.ent_new_name.grid(row=0, column=0, padx=5, pady=5)

            self.ent_new_email = ctk.CTkEntry(tab_user, placeholder_text="Correo electrónico", width=180)
            self.ent_new_email.grid(row=0, column=1, padx=5, pady=5)

            self.ent_new_pass = ctk.CTkEntry(tab_user, placeholder_text="Contraseña", show="*", width=120)
            self.ent_new_pass.grid(row=0, column=2, padx=5, pady=5)

            self.cmb_new_role = ctk.CTkOptionMenu(tab_user, values=["USER", "ADMIN"], width=90)
            self.cmb_new_role.grid(row=0, column=3, padx=5, pady=5)

            btn_crear_u = ctk.CTkButton(tab_user, text="Agregar Usuario", fg_color="#2E7D32", command=self.registrar_nuevo_usuario)
            btn_crear_u.grid(row=1, column=0, columnspan=4, padx=5, pady=5, sticky="ew")

            self.cmb_delete_user = ctk.CTkOptionMenu(tab_user, values=["Cargando..."], width=350)
            self.cmb_delete_user.grid(row=2, column=0, columnspan=3, padx=5, pady=10)

            btn_del_u = ctk.CTkButton(tab_user, text="Eliminar", fg_color="#D32F2F", command=self.eliminar_usuario)
            btn_del_u.grid(row=2, column=3, padx=5, pady=10, sticky="ew")
            self.cargar_lista_usuarios()

            # Sub-panel Categorías y Tags
            self.ent_new_cat = ctk.CTkEntry(tab_categorias_admin, placeholder_text="Nueva Categoría...", width=200)
            self.ent_new_cat.pack(pady=5)
            btn_cat = ctk.CTkButton(tab_categorias_admin, text="Agregar Categoría", command=self.agregar_categoria)
            btn_cat.pack(pady=2)

            self.ent_new_tag = ctk.CTkEntry(tab_categorias_admin, placeholder_text="Nuevo Tag...", width=200)
            self.ent_new_tag.pack(pady=5)
            btn_tag = ctk.CTkButton(tab_categorias_admin, text="Agregar Tag", command=self.agregar_tag)
            btn_tag.pack(pady=2)

        # 3. Filtro por Categorías (Fila 2)
        frame_filtro = ctk.CTkFrame(self, fg_color="transparent")
        frame_filtro.grid(row=2, column=0, padx=20, pady=(5, 0), sticky="ew")

        ctk.CTkLabel(frame_filtro, text="🔍 Filtrar por Categoría:", font=("Roboto", 12, "bold")).pack(side="left", padx=(0, 10))
        
        self.cmb_filtro_cat = ctk.CTkOptionMenu(frame_filtro, values=list(self.cat_filter_dict.keys()), command=lambda choice: self.cargar_articulos())
        self.cmb_filtro_cat.pack(side="left")

        # 4. FEED DE PUBLICACIONES (Fila 3)
        self.area_feed = ctk.CTkScrollableFrame(self)
        self.area_feed.grid(row=3, column=0, padx=20, pady=(10, 15), sticky="nsew")

        self.cargar_articulos()

    # -------------------------------------------------------------
    # OBTENER CATEGORÍAS Y ETIQUETAS DE UN ARTÍCULO
    # -------------------------------------------------------------
    def obtener_categorias_y_etiquetas(self, cursor, article_id):
        """Obtiene las categorías y etiquetas de un artículo mediante funciones de la BD."""
        cats, tags = [], []
        try:
            # Categorías (Llamada a función fn_get_article_categories)
            ref_cats = cursor.callfunc("fn_get_article_categories", oracledb.DB_TYPE_CURSOR, [article_id])
            cats = [r[0] for r in ref_cats.fetchall()]
            ref_cats.close()

            # Etiquetas (Llamada a función fn_get_article_tags)
            ref_tags = cursor.callfunc("fn_get_article_tags", oracledb.DB_TYPE_CURSOR, [article_id])
            tags = [r[0] for r in ref_tags.fetchall()]
            ref_tags.close()
            
        except Exception as e:
            print(f"Error obteniendo categorías y etiquetas del artículo {article_id}: {e}")
        
        return cats, tags

    # -------------------------------------------------------------
    # MOSTRAR Y FILTRAR PUBLICACIONES
    # -------------------------------------------------------------
    def cargar_articulos(self):
        for widget in self.area_feed.winfo_children():
            widget.destroy()

        cat_seleccionada = self.cmb_filtro_cat.get() if hasattr(self, 'cmb_filtro_cat') else "Todas las categorías"
        cat_id_filtro = self.cat_filter_dict.get(cat_seleccionada, None)

        try:
            conn = self.conectar_db()
            cursor = conn.cursor()
            ref_cursor = cursor.callfunc("fn_get_articles", oracledb.DB_TYPE_CURSOR)

            for art_id, title, date, text, author in ref_cursor.fetchall():
                # Llamada al nuevo método renombrado
                cats, tags = self.obtener_categorias_y_etiquetas(cursor, art_id)

                # Si hay un filtro de categoría activo y el post no la contiene, lo saltamos
                if cat_id_filtro is not None and cat_seleccionada not in cats:
                    continue

                card = ctk.CTkFrame(self.area_feed, corner_radius=8)
                card.pack(fill="x", pady=8, padx=5)

                # Encabezado del Post
                header = ctk.CTkLabel(card, text=f"📌 {title} | Por: {author} ({date})", font=("Roboto", 13, "bold"))
                header.pack(anchor="w", padx=10, pady=(8, 2))

                # Texto del Post
                body = ctk.CTkLabel(card, text=str(text), wraplength=650, justify="left", font=("Roboto", 11))
                body.pack(anchor="w", padx=10, pady=(2, 5))

                # --- SECCIÓN DE CATEGORÍAS Y ETIQUETAS/TAGS EN EL POST ---
                frame_etiquetas_post = ctk.CTkFrame(card, fg_color="transparent")
                frame_etiquetas_post.pack(anchor="w", padx=10, pady=(0, 5))

                str_cats = "📁 " + ", ".join(cats) if cats else "📁 Sin Categoría"
                lbl_categorias_post = ctk.CTkLabel(frame_etiquetas_post, text=str_cats, font=("Roboto", 10, "italic"), text_color="#64B5F6")
                lbl_categorias_post.pack(side="left", padx=(0, 15))

                str_tags = "🏷️ " + " ".join([f"#{t}" for t in tags]) if tags else "🏷️ Sin Tags"
                lbl_tags_post = ctk.CTkLabel(frame_etiquetas_post, text=str_tags, font=("Roboto", 10, "bold"), text_color="#FFB74D")
                lbl_tags_post.pack(side="left")

                if self.current_user_role == "ADMIN":
                    btn_borrar_art = ctk.CTkButton(card, text="Eliminar Post", fg_color="#D32F2F", height=22, width=90,
                                                   command=lambda id_art=art_id: self.eliminar_articulo(id_art))
                    btn_borrar_art.pack(anchor="e", padx=10, pady=2)

                # Sección de Comentarios
                frame_comentarios = ctk.CTkFrame(card, fg_color="#1E1E1E")
                frame_comentarios.pack(fill="x", padx=10, pady=5)

                ref_comms = cursor.callfunc("fn_get_comments", oracledb.DB_TYPE_CURSOR, [art_id])
                for comm_id, c_text, c_date, c_author in ref_comms.fetchall():
                    c_box = ctk.CTkFrame(frame_comentarios, fg_color="transparent")
                    c_box.pack(fill="x", pady=2)
                    
                    lbl_c = ctk.CTkLabel(c_box, text=f"💬 {c_author} ({c_date}): {c_text}", font=("Roboto", 10), wraplength=500, justify="left")
                    lbl_c.pack(side="left", padx=5)

                    if self.current_user_role == "ADMIN":
                        btn_del_c = ctk.CTkButton(c_box, text="X", fg_color="#B71C1C", width=20, height=18,
                                                  command=lambda id_c=comm_id: self.eliminar_comentario(id_c))
                        btn_del_c.pack(side="right", padx=5)
                ref_comms.close()

                # Añadir Comentario
                f_add_c = ctk.CTkFrame(card, fg_color="transparent")
                f_add_c.pack(fill="x", padx=10, pady=(0, 8))
                ent_c = ctk.CTkEntry(f_add_c, placeholder_text="Escribe un comentario...", height=25)
                ent_c.pack(side="left", fill="x", expand=True, padx=(0, 5))
                btn_c = ctk.CTkButton(f_add_c, text="Comentar", height=25, width=80,
                                      command=lambda id_a=art_id, txt=ent_c: self.agregar_comentario(id_a, txt))
                btn_c.pack(side="right")

            ref_cursor.close()
            cursor.close()
            conn.close()

        except Exception as e:
            print(f"Error cargando artículos: {e}")

    # -------------------------------------------------------------
    # AUXILIARES Y ADMINISTRACIÓN
    # -------------------------------------------------------------
    def guardar_articulo(self):
        titulo = self.ent_titulo.get().strip()
        texto = self.txt_texto.get("1.0", "end-1c").strip()

        if not titulo or not texto:
            messagebox.showwarning("Atención", "Título y contenido son obligatorios.")
            return

        try:
            conn = self.conectar_db()
            cursor = conn.cursor()
            
            
            art_id_var = cursor.var(oracledb.NUMBER)
            cursor.callproc("sp_add_article", [self.current_user_id, titulo, texto, art_id_var])
            nuevo_art_id = int(art_id_var.getvalue())

            for chk, cat_id in self.dict_categories.items():
                if chk.get() == 1:
                    cursor.callproc("sp_link_article_category", [nuevo_art_id, cat_id])

            for chk, tag_id in self.dict_tags.items():
                if chk.get() == 1:
                    cursor.callproc("sp_link_article_tag", [nuevo_art_id, tag_id])

            cursor.close()
            conn.close()

            self.ent_titulo.delete(0, "end")
            self.txt_texto.delete("1.0", "end")
            self.cargar_articulos()
            messagebox.showinfo("Éxito", "Artículo publicado correctamente.")

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo publicar: {e}")

    def agregar_comentario(self, article_id, entry_widget):
        texto = entry_widget.get().strip()
        if not texto:
            return
        try:
            conn = self.conectar_db()
            cursor = conn.cursor()
            cursor.callproc("sp_add_comment", [article_id, self.current_user_id, texto])
            cursor.close()
            conn.close()
            self.cargar_articulos()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo agregar comentario: {e}")

    def registrar_nuevo_usuario(self):
        nombre = self.ent_new_name.get().strip()
        email = self.ent_new_email.get().strip()
        password = self.ent_new_pass.get().strip()
        role = self.cmb_new_role.get()

        if not nombre or not email or not password:
            messagebox.showwarning("Atención", "Campos obligatorios.")
            return

        try:
            conn = self.conectar_db()
            cursor = conn.cursor()
            cursor.callproc("sp_create_user", [nombre, email, password, role])
            cursor.close()
            conn.close()
            messagebox.showinfo("Éxito", "Usuario creado.")
            self.cargar_lista_usuarios()
        except Exception as e:
            messagebox.showerror("Error", f"{e}")

    def cargar_lista_usuarios(self):
        try:
            conn = self.conectar_db()
            cursor = conn.cursor()
            ref_u = cursor.callfunc("fn_get_users", oracledb.DB_TYPE_CURSOR)
            
            self.lista_users_dict = {}
            opciones = []
            for u_id, u_name, u_email, u_role in ref_u.fetchall():
                label = f"{u_id} - {u_name} ({u_role})"
                opciones.append(label)
                self.lista_users_dict[label] = u_id
            
            ref_u.close()
            cursor.close()
            conn.close()

            if opciones:
                self.cmb_delete_user.configure(values=opciones)
                self.cmb_delete_user.set(opciones[0])
        except Exception as e:
            print(f"Error cargando usuarios: {e}")

    def eliminar_usuario(self):
        seleccion = self.cmb_delete_user.get()
        if seleccion in self.lista_users_dict:
            u_id = self.lista_users_dict[seleccion]
            if u_id == self.current_user_id:
                messagebox.showwarning("Atención", "No puedes eliminar tu propia cuenta activa.")
                return
            try:
                conn = self.conectar_db()
                cursor = conn.cursor()
                cursor.callproc("sp_delete_user", [u_id])
                cursor.close()
                conn.close()
                messagebox.showinfo("Éxito", "Usuario eliminado.")
                self.cargar_lista_usuarios()
            except Exception as e:
                messagebox.showerror("Error", f"{e}")

    def agregar_categoria(self):
        cat = self.ent_new_cat.get().strip()
        if cat:
            try:
                conn = self.conectar_db()
                cursor = conn.cursor()
                cursor.callproc("sp_create_category", [cat])
                cursor.close()
                conn.close()
                self.pantalla_principal()
            except Exception as e:
                messagebox.showerror("Error", f"{e}")

    def agregar_tag(self):
        tag = self.ent_new_tag.get().strip()
        if tag:
            try:
                conn = self.conectar_db()
                cursor = conn.cursor()
                cursor.callproc("sp_create_tag", [tag])
                cursor.close()
                conn.close()
                self.pantalla_principal()
            except Exception as e:
                messagebox.showerror("Error", f"{e}")

    def eliminar_articulo(self, article_id):
        if messagebox.askyesno("Confirmar", "¿Eliminar esta publicación?"):
            try:
                conn = self.conectar_db()
                cursor = conn.cursor()
                cursor.callproc("sp_delete_article", [article_id])
                cursor.close()
                conn.close()
                self.cargar_articulos()
            except Exception as e:
                messagebox.showerror("Error", f"{e}")

    def eliminar_comentario(self, comment_id):
        try:
            conn = self.conectar_db()
            cursor = conn.cursor()
            cursor.callproc("sp_delete_comment", [comment_id])
            cursor.close()
            conn.close()
            self.cargar_articulos()
        except Exception as e:
            messagebox.showerror("Error", f"{e}")

    def cargar_opciones_cat_tag(self, frame_cat, frame_tag):
        self.dict_categories.clear()
        self.dict_tags.clear()
        self.cat_filter_dict = {"Todas las categorías": None}

        try:
            conn = self.conectar_db()
            cursor = conn.cursor()

            # Cargar Categorías
            ref_cat = cursor.callfunc("fn_get_categories", oracledb.DB_TYPE_CURSOR)
            for cat_id, cat_name in ref_cat.fetchall():
                chk = ctk.CTkCheckBox(frame_cat, text=cat_name)
                chk.pack(anchor="w", padx=5, pady=2)
                self.dict_categories[chk] = cat_id
                self.cat_filter_dict[cat_name] = cat_id
            ref_cat.close()

            # Cargar Tags
            ref_tag = cursor.callfunc("fn_get_tags", oracledb.DB_TYPE_CURSOR)
            for tag_id, tag_name in ref_tag.fetchall():
                chk = ctk.CTkCheckBox(frame_tag, text=tag_name)
                chk.pack(anchor="w", padx=5, pady=2)
                self.dict_tags[chk] = tag_id
            ref_tag.close()

            cursor.close()
            conn.close()
        except Exception as e:
            print(f"Error cargando opciones: {e}")

    def cerrar_sesion(self):
        self.current_user_id = None
        self.current_user_name = ""
        self.current_user_role = "USER"
        self.pantalla_login()

if __name__ == "__main__":
    app = AppBlog()
    app.mainloop()