-- =============================================================
-- SCRIPT 2: PROCEDIMIENTOS ALMACENADOS Y FUNCIONES (PL/SQL)
-- =============================================================

-- 1. PROCEDIMIENTOS ALMACENADOS
----------------------------------------------------------------

-- Autenticación
CREATE OR REPLACE PROCEDURE sp_login (
    p_email IN VARCHAR2,
    p_password IN VARCHAR2,
    p_user_id OUT NUMBER,
    p_name OUT VARCHAR2,
    p_role OUT VARCHAR2
) AS
    v_db_password VARCHAR2(100);
BEGIN
    SELECT user_id, name, password, role 
    INTO p_user_id, p_name, v_db_password, p_role
    FROM users 
    WHERE LOWER(email) = LOWER(p_email);

    IF v_db_password != p_password THEN
        RAISE_APPLICATION_ERROR(-20001, 'Contraseña incorrecta.');
    END IF;
EXCEPTION
    WHEN NO_DATA_FOUND THEN
        RAISE_APPLICATION_ERROR(-20002, 'El correo electrónico no está registrado.');
END;
/

-- EXCLUSIVO ADMIN: Crear Usuario
CREATE OR REPLACE PROCEDURE sp_create_user (
    p_name IN VARCHAR2,
    p_email IN VARCHAR2,
    p_password IN VARCHAR2,
    p_role IN VARCHAR2
) AS
BEGIN
    INSERT INTO users (name, email, password, role) 
    VALUES (p_name, LOWER(p_email), p_password, NVL(p_role, 'USER'));
    COMMIT;
EXCEPTION
    WHEN DUP_VAL_ON_INDEX THEN
        RAISE_APPLICATION_ERROR(-20003, 'El correo electrónico ya existe.');
END;
/

-- EXCLUSIVO ADMIN: Eliminar Usuario
CREATE OR REPLACE PROCEDURE sp_delete_user (
    p_user_id IN NUMBER
) AS
BEGIN
    DELETE FROM users WHERE user_id = p_user_id;
    COMMIT;
END;
/

-- EXCLUSIVO ADMIN: Crear Categoría
CREATE OR REPLACE PROCEDURE sp_create_category (
    p_name IN VARCHAR2
) AS
BEGIN
    INSERT INTO categories (name) VALUES (p_name);
    COMMIT;
EXCEPTION
    WHEN DUP_VAL_ON_INDEX THEN
        RAISE_APPLICATION_ERROR(-20004, 'La categoría ya existe.');
END;
/

-- EXCLUSIVO ADMIN: Crear Tag
CREATE OR REPLACE PROCEDURE sp_create_tag (
    p_name IN VARCHAR2
) AS
BEGIN
    INSERT INTO tags (name) VALUES (p_name);
    COMMIT;
EXCEPTION
    WHEN DUP_VAL_ON_INDEX THEN
        RAISE_APPLICATION_ERROR(-20005, 'La etiqueta ya existe.');
END;
/

-- Publicar Artículo (Disponible para USER y ADMIN)
CREATE OR REPLACE PROCEDURE sp_add_article (
    p_user_id IN NUMBER,
    p_title IN VARCHAR2,
    p_text IN VARCHAR2,
    p_article_id OUT NUMBER 
) AS
BEGIN
    INSERT INTO articles (user_id, title, text) 
    VALUES (p_user_id, p_title, p_text)
    RETURNING article_id INTO p_article_id; 
    COMMIT;
END;
/

-- Vincular Categorías y Tags a un Artículo
CREATE OR REPLACE PROCEDURE sp_link_article_category (p_article_id IN NUMBER, p_category_id IN NUMBER) AS
BEGIN
    INSERT INTO article_categories (article_id, category_id) VALUES (p_article_id, p_category_id);
    COMMIT;
END;
/

CREATE OR REPLACE PROCEDURE sp_link_article_tag (p_article_id IN NUMBER, p_tag_id IN NUMBER) AS
BEGIN
    INSERT INTO article_tags (article_id, tag_id) VALUES (p_article_id, p_tag_id);
    COMMIT;
END;
/

-- Agregar Comentario (Disponible para USER y ADMIN)
CREATE OR REPLACE PROCEDURE sp_add_comment (
    p_article_id IN NUMBER,
    p_user_id IN NUMBER,
    p_text IN VARCHAR2
) AS
BEGIN
    INSERT INTO comments (article_id, user_id, text) 
    VALUES (p_article_id, p_user_id, p_text);
    COMMIT;
END;
/

-- EXCLUSIVO ADMIN: Eliminar Artículo
CREATE OR REPLACE PROCEDURE sp_delete_article (p_article_id IN NUMBER) AS
BEGIN
    DELETE FROM articles WHERE article_id = p_article_id;
    COMMIT;
END;
/

-- EXCLUSIVO ADMIN: Eliminar Comentario
CREATE OR REPLACE PROCEDURE sp_delete_comment (p_comment_id IN NUMBER) AS
BEGIN
    DELETE FROM comments WHERE comment_id = p_comment_id;
    COMMIT;
END;
/


-- 2. FUNCIONES DE CONSULTA
----------------------------------------------------------------

CREATE OR REPLACE FUNCTION fn_get_articles RETURN SYS_REFCURSOR AS
    v_cursor SYS_REFCURSOR;
BEGIN
    OPEN v_cursor FOR
        SELECT a.article_id, a.title, TO_CHAR(a.art_date, 'DD/MM/YYYY HH24:MI'), a.text, u.name 
        FROM articles a 
        JOIN users u ON a.user_id = u.user_id 
        ORDER BY a.article_id DESC;
    RETURN v_cursor;
END;
/

CREATE OR REPLACE FUNCTION fn_get_comments (p_article_id IN NUMBER) RETURN SYS_REFCURSOR AS
    v_cursor SYS_REFCURSOR;
BEGIN
    OPEN v_cursor FOR
        SELECT c.comment_id, c.text, TO_CHAR(c.comment_date, 'DD/MM/YYYY HH24:MI'), u.name
        FROM comments c
        JOIN users u ON c.user_id = u.user_id
        WHERE c.article_id = p_article_id
        ORDER BY c.comment_id ASC;
    RETURN v_cursor;
END;
/

CREATE OR REPLACE FUNCTION fn_get_users RETURN SYS_REFCURSOR AS
    v_cursor SYS_REFCURSOR;
BEGIN
    OPEN v_cursor FOR SELECT user_id, name, email, role FROM users ORDER BY name;
    RETURN v_cursor;
END;
/

CREATE OR REPLACE FUNCTION fn_get_categories RETURN SYS_REFCURSOR AS
    v_cursor SYS_REFCURSOR;
BEGIN
    OPEN v_cursor FOR SELECT category_id, name FROM categories ORDER BY name;
    RETURN v_cursor;
END;
/

CREATE OR REPLACE FUNCTION fn_get_tags RETURN SYS_REFCURSOR AS
    v_cursor SYS_REFCURSOR;
BEGIN
    OPEN v_cursor FOR SELECT tag_id, name FROM tags ORDER BY name;
    RETURN v_cursor;
END;
/

CREATE OR REPLACE FUNCTION fn_get_article_categories (p_article_id IN NUMBER)
RETURN SYS_REFCURSOR IS
    v_cursor SYS_REFCURSOR;
BEGIN
    OPEN v_cursor FOR
        SELECT c.name 
        FROM categories c 
        JOIN article_categories ac ON c.category_id = ac.category_id 
        WHERE ac.article_id = p_article_id;
        
    RETURN v_cursor;
END;
/

CREATE OR REPLACE FUNCTION fn_get_article_tags (p_article_id IN NUMBER)
RETURN SYS_REFCURSOR IS
    v_cursor SYS_REFCURSOR;
BEGIN
    OPEN v_cursor FOR
        SELECT t.name 
        FROM tags t 
        JOIN article_tags at ON t.tag_id = at.tag_id 
        WHERE at.article_id = p_article_id;
        
    RETURN v_cursor;
END;
/