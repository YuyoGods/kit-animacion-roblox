# Envia un script al Blender abierto (addon BlenderMCP). Uso: py bl.py mi_script.py
import os, socket, json, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
try:
    from config import BLENDER_MCP_PUERTO as PUERTO
except Exception:
    PUERTO = 9876
code = open(sys.argv[1], encoding='utf-8').read() if len(sys.argv)>1 else "import bpy; result = bpy.app.version_string"
s = socket.create_connection(("localhost", PUERTO), timeout=600)
s.sendall(json.dumps({"type":"execute_code","params":{"code":code}}).encode())
buf=b""
while True:
    ch=s.recv(65536)
    if not ch: break
    buf+=ch
    try: json.loads(buf); break
    except: pass
print(buf.decode(errors='replace'))
