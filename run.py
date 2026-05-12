import socket
from app import create_app

app = create_app()

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # No necesita conexión real, solo para obtener la interfaz de red activa
        s.connect(('8.8.8.8', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

if __name__ == '__main__':
    
    app.run(debug=True, host='0.0.0.0', port=5000)
