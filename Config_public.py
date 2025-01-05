import json, requests, os, traceback, getpass
from requests.auth import HTTPBasicAuth
config_file = 'C:\\Users\\Public\\Documents\\uiiai\\config.json'
class Config:
    def __init__(self):
        self.__dict__["activo"] = True
        self.esperas = {}
        self.esperas['oculto'] = (15, 600)
        self.esperas['fantasma'] = (5, 20)
        self.esperas['visible'] = (1, 7)
        self.esperas['frenesi'] = (5, 20)

        self.duraciones = {}
        self.duraciones['mostrarFantasma'] = (0.25,5)
        self.duraciones['quitar'] = (0.25,5)
        self.duraciones["mostrarVisible"] = (0.25, 5)

        self.probabilidades = {}
        self.probabilidades["cambiar_pos"] = 50
        self.probabilidades['fantasmoso'] = 90
        self.probabilidades['retorno'] = 20
        self.probabilidades['frenesi'] = 10
        self.probabilidades['tanteo'] = 50
    def guardar(self):
        if not os.path.exists(os.path.dirname(config_file)):
            os.makedirs(os.path.dirname(config_file))
        with open(config_file, 'w') as f:
            json.dump(self.__dict__, f)
    def cargar_local(self):
        try:
            with open(config_file, 'r') as f:
                data = json.load(f)
                self.__dict__.update(data)
        except:
            print("Usando por defecto")
    def cargar(self):
        self.cargar_local()
if __name__ == '__main__':
    config = Config()
    while True:
        opcion = int(input("1. Guardar\n2. Cargar\n3. Mostrar\n4. Cambiar\n5. Salir\n"))
        if opcion == 1:
            config.guardar()
        elif opcion == 2:
            config.cargar()
        elif opcion == 3:
            print(config.__dict__)
        elif opcion == 4:
            subdict = input("Subdict: ")
            clave = input("Clave: ")
            valor = input("Valor: ")
            if subdict in config.__dict__ and clave in config.__dict__[subdict]:
                config.__dict__[subdict][clave] = valor
            else:
                print("Clave no válida")
        elif opcion == 5:
            break
        else:
            print("Opción no válida")
            pass
