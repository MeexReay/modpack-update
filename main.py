from tkinter import *
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox
from difflib import SequenceMatcher
import win32console
import win32gui
import tempfile
import requests
import zipfile
import atexit
import toml
import json
import sys
import os
import re

win32gui.ShowWindow(win32console.GetConsoleWindow(),0)

data_path = os.path.dirname(__file__)

def get_name(path,loader):
    zip = zipfile.ZipFile(path, 'r')
    if loader == "forge":
        return toml.loads(zip.read("META-INF/mods.toml").decode("utf8"))["mods"][0]["displayName"]
    elif loader == "fabric":
        return json.loads(zip.read("fabric.mod.json"))["name"]
    return None
def find_mod(name,version,loader,regex_name): 
    data = None
    md = _find_modrinth(name,version,loader,regex_name)
    if md != None: data = md
    else:
        cf = _find_curseforge(name,version,loader,regex_name)
        if cf != None: data = cf
    if data != None and not data[0].endswith(".jar"):
        data = None
    return data
def regex_name(name):
    return re.sub("([\(\[]).*?([\)\]])", "", name.lower().replace(" ",""))
def _find_modrinth(query,version,loader,regex_query): 
    resp = requests.get("https://api.modrinth.com/v2/search",params={"query":query}).json()
    if "hits" in resp and len(resp["hits"]) > 0:
        hit = resp["hits"][0]
        title = regex_name(hit["title"])
        r = SequenceMatcher(None, title, regex_query).ratio()
        if r > 0.8:
            if loader in hit["categories"]:
                resp = requests.get(f"https://api.modrinth.com/v2/project/{hit['project_id']}/version",
                                    params={"loaders":f'["{loader}"]',"game_versions":f'["{version}"]'}).json()
                if len(resp) > 0 and len(resp[0]["files"]) > 0:
                    return [resp[0]["files"][0]["filename"],requests.get(resp[0]["files"][0]["url"]).content]
    return None
def _find_curseforge(query,version,loader,regex_query): 
    resp = requests.get("https://api.curseforge.com/v1/mods/search",
            headers={"x-api-key": "$2a$10$WldWeyy9nRXLI9Dbjyr7UuES2Dy9fvKbBfMmQHUwHWNR8daJA2FI.","Accept":"application/json"},
            params={"gameId":432, 
                    "modLoaderType":loader.title(), 
                    "gameVersion":version,
                    "searchFilter":query}).json()["data"]
    if len(resp) > 0:
        resp = resp[0]
        title = regex_name(resp["name"])
        if SequenceMatcher(None, title, regex_query).ratio() > 0.8:
            files = requests.get(f"https://api.curseforge.com/v1/mods/{resp['id']}/files",
                headers={"x-api-key": "$2a$10$WldWeyy9nRXLI9Dbjyr7UuES2Dy9fvKbBfMmQHUwHWNR8daJA2FI.","Accept":"application/json"},
                params={"modLoaderType":loader.title(),"gameVersion":version}).json()["data"]
            if len(files) > 0:
                return [files[0]["fileName"],requests.get(files[0]["downloadUrl"]).content]
    return None

window = Tk()
window.title("ModpackUpdate")
window.geometry("350x305")
window.config(bg="#333")
window.resizable(False, False)
window.iconbitmap(os.path.join(data_path,"favicon.ico"))

versions = ['1.20.1', '1.20', '1.19.4', '1.19.3', '1.19.2', '1.19.1', '1.19', '1.18.2', '1.18.1', '1.18', 
            '1.17.1', '1.17', '1.16.5', '1.16.4', '1.16.3', '1.16.2', '1.16.1', '1.16', '1.15.2', '1.15.1', '1.15', 
            '1.14.4', '1.14.3', '1.14.2', '1.14.1', '1.14']
ttk.Style().configure("TRadiobutton", background = "#333",
                  foreground = "white", font = ('Arial', 10))

files = None
folder = None

def choose_mods():
    global files,btn_CM
    files = filedialog.askopenfilenames(title="Выберите моды для обновления",filetypes=[('JAR files', '.jar')])
    if not (not files):
        btn_CM["state"] = "disabled"
def choose_folder():
    global folder,btn_folder
    folder = filedialog.askdirectory(title="Выберите папку для новых модов")
    if not (not folder):
        btn_folder["state"] = "disabled"

def temporaryFilename(prefix=None, suffix='tmp', dir=None, text=False, removeOnExit=True):
    if prefix is None:
        prefix = "%s_%d_" % (os.path.basename(sys.argv[0]), os.getpid())

    (fileHandle, path) = tempfile.mkstemp(prefix=prefix, suffix=suffix, dir=dir, text=text)
    os.close(fileHandle)

    def removeFile(path):
        os.remove(path)

    if removeOnExit:
        atexit.register(removeFile, path)

    return path

def install_fabric(version):
    path = temporaryFilename(suffix=".jar")
    with open(path,"wb") as f:
        f.write(requests.get("https://maven.fabricmc.net/net/fabricmc/fabric-installer/0.11.2/fabric-installer-0.11.2.jar").content)
    os.system("java -jar "+path+" client -mcversion "+version)

def install_forge(version):
    url = {
        '1.20.1':"https://maven.minecraftforge.net/net/minecraftforge/forge/1.20.1-47.1.0/forge-1.20.1-47.1.0-installer.jar",
        '1.20':"https://maven.minecraftforge.net/net/minecraftforge/forge/1.20-46.0.14/forge-1.20-46.0.14-installer.jar", 
        '1.19.4':"https://maven.minecraftforge.net/net/minecraftforge/forge/1.19.4-45.1.0/forge-1.19.4-45.1.0-installer.jar",
        '1.19.3':"https://maven.minecraftforge.net/net/minecraftforge/forge/1.19.3-44.1.0/forge-1.19.3-44.1.0-installer.jar", 
        '1.19.2':"https://maven.minecraftforge.net/net/minecraftforge/forge/1.19.2-43.2.0/forge-1.19.2-43.2.0-installer.jar", 
        '1.19.1':"https://maven.minecraftforge.net/net/minecraftforge/forge/1.19.1-42.0.9/forge-1.19.1-42.0.9-installer.jar", 
        '1.19':"https://maven.minecraftforge.net/net/minecraftforge/forge/1.19-41.1.0/forge-1.19-41.1.0-installer.jar", 
        '1.18.2':"https://maven.minecraftforge.net/net/minecraftforge/forge/1.18.2-40.2.0/forge-1.18.2-40.2.0-installer.jar", 
        '1.18.1':"https://maven.minecraftforge.net/net/minecraftforge/forge/1.18.1-39.1.0/forge-1.18.1-39.1.0-installer.jar", 
        '1.18':"https://maven.minecraftforge.net/net/minecraftforge/forge/1.18-38.0.17/forge-1.18-38.0.17-installer.jar", 
        '1.17.1':"https://maven.minecraftforge.net/net/minecraftforge/forge/1.17.1-37.1.1/forge-1.17.1-37.1.1-installer.jar", 
        '1.16.5':"https://maven.minecraftforge.net/net/minecraftforge/forge/1.16.5-36.2.34/forge-1.16.5-36.2.34-installer.jar", 
        '1.16.4':"https://maven.minecraftforge.net/net/minecraftforge/forge/1.16.4-35.1.4/forge-1.16.4-35.1.4-installer.jar", 
        '1.16.3':"https://maven.minecraftforge.net/net/minecraftforge/forge/1.16.3-34.1.0/forge-1.16.3-34.1.0-installer.jar", 
        '1.16.2':"https://maven.minecraftforge.net/net/minecraftforge/forge/1.16.2-33.0.61/forge-1.16.2-33.0.61-installer.jar", 
        '1.16.1':"https://maven.minecraftforge.net/net/minecraftforge/forge/1.16.1-32.0.108/forge-1.16.1-32.0.108-installer.jar", 
        '1.15.2':"https://maven.minecraftforge.net/net/minecraftforge/forge/1.15.2-31.2.57/forge-1.15.2-31.2.57-installer.jar", 
        '1.15.1':"https://maven.minecraftforge.net/net/minecraftforge/forge/1.15.1-30.0.51/forge-1.15.1-30.0.51-installer.jar", 
        '1.15':"https://maven.minecraftforge.net/net/minecraftforge/forge/1.15-29.0.4/forge-1.15-29.0.4-installer.jar", 
        '1.14.4':"https://maven.minecraftforge.net/net/minecraftforge/forge/1.14.4-28.2.26/forge-1.14.4-28.2.26-installer.jar", 
        '1.14.3':"https://maven.minecraftforge.net/net/minecraftforge/forge/1.14.3-27.0.60/forge-1.14.3-27.0.60-installer.jar", 
        '1.14.2':"https://maven.minecraftforge.net/net/minecraftforge/forge/1.14.2-26.0.63/forge-1.14.2-26.0.63-installer.jar"
        }[version]
    path = temporaryFilename(suffix=".jar")
    with open(path,"wb") as f:
        f.write(requests.get(url).content)
    os.system("java -jar "+path)

def start_modsupdate():
    global pb,old_loader,loader,folder,files,versions,window,btn_start

    if folder == None:
        messagebox.showerror("Ошибка!","Укажите папку назначения,\nто есть папку куда будут \nзаписаны новые моды")
        return
    if files == None:
        messagebox.showerror("Ошибка!","Укажите моды которые\nнадо обновить")
        return
    
    btn_start["state"] = "disabled"

    pb.config(maximum=len(files)*2)

    olderModLoader = "forge" if old_loader.get() else "fabric"
    newerModLoader = "forge" if loader.get() else "fabric"
    version = versions.get()

    another = "fabric" if olderModLoader == "forge" else "forge"

    names = []

    regex_names = {}

    invalid_name = []
    invalid_found = []

    for i in files:
        name = None
        try:
            name = get_name(i,olderModLoader)
            if name != None:
                names.append(name)
        except Exception:
            pass
        if name != None:
            regex_names[name] = regex_name(name)
            pb.step()
            window.update()
        else:
            invalid_name.append(os.path.basename(i))
    pb.config(maximum=len(names)*2,value=pb["value"])

    for i in names:
        try:
            data = find_mod(i,version,newerModLoader,regex_names[i])
        except Exception:
            data = None
        if data != None:
            with open(os.path.join(folder,data[0]),"wb") as f:
                f.write(data[1])
                f.close()
        else:
            invalid_found.append(i)
        pb.step()
        window.update()

    resp_win = Toplevel()
    resp_win.title("Готово!")
    resp_win.config(bg="#333")
    resp_win.resizable(True, True)
    resp_win.iconbitmap(os.path.join(data_path,"favicon.ico"))

    y = 0

    if len(invalid_name) != 0:
        Label(resp_win, text='Не найдено название: ', font=('Arial', 13), background="#333", foreground="#ddd").place(x=10,y=y+10)
        y += 20
        for i in invalid_name:
            Label(resp_win, text=i, font=('Arial', 10), background="#333", foreground="#ddd").place(x=10,y=y+10)
            y += 14
        y += 20
    if len(invalid_found) != 0:
        Label(resp_win, text='Не найден мод: ', font=('Arial', 13), background="#333", foreground="#ddd").place(x=10,y=y+10)
        y += 20
        for i in invalid_found:
            Label(resp_win, text=i, font=('Arial', 10), background="#333", foreground="#ddd").place(x=10,y=y+10)
            y += 20
    if len(invalid_found) == 0 and len(invalid_name) == 0:
        Label(resp_win, text='Ошибок нет!', font=('Arial', 13), background="#333", foreground="#ddd").place(x=10,y=y+10)
        y += 20
    f = os.path.realpath(folder)
    def open_folder():
        os.startfile(f)
    Button(resp_win, text='Открыть папку', command=open_folder, relief=FLAT).place(x=10,y=y+30)
    y += 35
    if newerModLoader == "forge":
        Button(resp_win, text='Установить Forge', command=lambda:install_forge(version), relief=FLAT).place(x=10,y=y+30)
    elif newerModLoader == "fabric":
        Button(resp_win, text='Установить Fabric', command=lambda:install_fabric(version), relief=FLAT).place(x=10,y=y+30)
    
    resp_win.geometry("350x"+str(y+90))
    resp_win.minsize(350,y+70)

    resp_win.grab_set()
    
    pb["value"] = 0
    btn_start["state"] = "normal"
    btn_folder["state"] = "normal"
    btn_CM["state"] = "normal"
    files = None
    folder = None

title = Label(window, text='ModpackUpdate', font=('Arial', 30, 'bold'), background="#333", foreground="#ddd")
title.place(x=10,y=10)

choose_version_label = Label(window, text='Выберите версию для обновления модов', font=('Arial', 10), background="#333", foreground="#ddd")
choose_version_label.place(x=10,y=60)
versions = ttk.Combobox(window, values=versions, state="readonly")
versions.set("1.20.1")
versions.place(x=12,y=85)

old_loader = BooleanVar()
old_loader.set(True)
choose_loader_label = Label(window, text='Выберите текущий загрузчик', font=('Arial', 10), background="#333", foreground="#ddd")
choose_loader_label.place(x=10,y=120)
old_forge = ttk.Radiobutton(window, text='Forge', variable=old_loader, value=True)
old_forge.place(x=10,y=140)
old_fabric = ttk.Radiobutton(window, text='Fabric', variable=old_loader, value=False)
old_fabric.place(x=70,y=140)

loader = BooleanVar()
loader.set(True)
choose_loader_label = Label(window, text='Выберите новый загрузчик', font=('Arial', 10), background="#333", foreground="#ddd")
choose_loader_label.place(x=10,y=170)
forge = ttk.Radiobutton(window, text='Forge', variable=loader, value=True)
forge.place(x=10,y=190)
fabric = ttk.Radiobutton(window, text='Fabric', variable=loader, value=False)
fabric.place(x=70,y=190)

btn_CM = Button(window, text='Выбрать моды', command=choose_mods, relief=FLAT)
btn_CM.place(x=10,y=230)
btn_folder = Button(window, text='Выбрать папку назначения', command=choose_folder, relief=FLAT)
btn_folder.place(x=110,y=230)
btn_start = Button(window, text='Начать', command=start_modsupdate, relief=FLAT)
btn_start.place(x=10,y=270)

pb = ttk.Progressbar(window, mode="determinate", length=270, value=0, maximum=100)
pb.place(x=70,y=270,height=26)

window.mainloop()