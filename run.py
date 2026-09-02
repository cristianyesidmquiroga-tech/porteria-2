from app import create_app

app = create_app()

if __name__ == '__main__':
    # Solo para desarrollo local. En produccion el contenedor arranca con
    # gunicorn (ver docker/entrypoint.sh); nunca con el servidor de Flask.
    app.run(debug=False, host='127.0.0.1', port=5000, use_reloader=False)
