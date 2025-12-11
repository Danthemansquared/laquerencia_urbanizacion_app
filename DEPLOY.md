# Guía de Despliegue en Streamlit Cloud

## Paso 1: Subir cambios a GitHub

Si aún no has subido los últimos cambios, puedes usar GitHub Desktop o ejecutar:

```bash
git push origin main
```

## Paso 2: Conectar con Streamlit Cloud

1. Ve a [https://share.streamlit.io/](https://share.streamlit.io/)
2. Inicia sesión con tu cuenta de GitHub
3. Haz clic en "New app"
4. Selecciona tu repositorio: `Danthemansquared/laquerencia_urbanizacion_app`
5. Configura:
   - **Main file path**: `app.py`
   - **App URL**: (opcional) puedes personalizar la URL
6. Haz clic en "Deploy!"

## Paso 3: Configurar la URL de datos automática (Opcional)

Si quieres que los datos se carguen automáticamente:

1. En Streamlit Cloud, ve a tu aplicación desplegada
2. Haz clic en "Settings" (⚙️) en el menú superior derecho
3. Ve a la pestaña "Secrets"
4. Agrega el siguiente contenido:

```toml
DEFAULT_DATA_URL = "TU_URL_AQUI"
```

**Para Google Sheets:**
- Copia la URL completa de tu Google Sheet (debe estar compartido como "Cualquiera con el enlace")
- Ejemplo: `https://docs.google.com/spreadsheets/d/1UHMIprNilmgJmSL380tbpm_2bJ5OH-eM/edit?usp=drive_link`

**Para Google Drive:**
- Copia la URL del archivo Excel en Drive
- Ejemplo: `https://drive.google.com/file/d/ABC123...`

5. Haz clic en "Save"
6. La aplicación se recargará automáticamente

## Paso 4: Compartir tu aplicación

Una vez desplegada, tendrás una URL como:
`https://tu-app.streamlit.app`

¡Comparte esta URL con quien quieras!

## Notas importantes

- La aplicación se actualiza automáticamente cuando haces push a GitHub
- Los secrets son privados y solo tú puedes verlos
- Si no configuras `DEFAULT_DATA_URL`, los usuarios pueden cargar el archivo manualmente o desde URL

