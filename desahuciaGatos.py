import os, psutil
if __name__ == '__main__':
    for process in psutil.process_iter():
        try:
            if "inocente" in process.name() or "uiiai" in process.name():
                process.kill()
        except:
            pass
    ruta_base = f"C:\\Users\\{os.getlogin()}\\AppData\\Roaming\\Microsoft\\Windows\\Start Menu\\Programs\\Startup"
    ruta_inocente = os.path.join(ruta_base, "inocente.exe")
    if os.path.exists(ruta_inocente):
        os.remove(ruta_inocente)
    ruta_uiiai = os.path.join(ruta_base, "uiiai.exe")
    if os.path.exists(ruta_uiiai):
        os.remove(ruta_uiiai)
    ruta_uiiai_public = os.path.join(ruta_base, "uiiai_public.exe")
    if os.path.exists(ruta_uiiai_public):
        os.remove(ruta_uiiai_public)
    print("El gato ha sido desahuciado")
    os.system("pause")