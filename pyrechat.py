import pyrebase
import pyperclip
import pyautogui
import requests
import json
import os, shutil
import time, datetime

with open("firebase-secrets.json", "r") as file:
	config = json.load(file)

firebase = pyrebase.initialize_app(config)
db = firebase.database()
storage = firebase.storage()

def append_taken_files():
	list = []
	for file in storage.list_files():
		file_name = file.name
		if file_name != "& clipboard.txt":
			list.append(file_name)
	return list

def append_taken_text_files():
	list = []
	for file in storage.list_files():
		file_name = file.name
		if file_name[file_name.rfind("."):] not in excluded_file_extensions and file_name != "& clipboard.txt":
			list.append(file_name)
	return list

username = ""

taken_files = append_taken_files()
excluded_file_extensions = [".wav", ".mp3", ".ogg", ".aac", ".wma", ".m4a", ".flac", ".alac", ".avi", ".mp4", ".mov", ".mkv", ".mpg", ".mts", ".flv", ".bmp", ".png", ".gif", ".jpg", ".psd", ".heif", ".webp", ".avif", ".docs", ".xlsx", ".pptx", ".odt", ".odp", ".ods", ".rtf", ".pdf", ".zip", ".rar", ".exe", ".msi", ".dmg"]
taken_text_files = append_taken_text_files()

print_data = False

def stream_handler(message):
	global username, print_data, taken_files, taken_text_files, excluded_file_extensions
	try:
		data = message["data"]
		for key in data:
			value = data[key]
			if "@ " in key and "send to firebase storage" in key and f"@ {username}" not in key:
				if value == "clipboard":
					print(f"~\n{key}{value}\n# ", end = "")
				else:
					print(f"~\n{key}\"{value}\"\n# ", end = "")
					taken_files.append(value)
					file_format = value[value.rfind("."):]
					if file_format not in excluded_file_extensions:
						taken_text_files.append(value)
			elif "@ " in key and value == "connected" and f"@ {username}" not in key:
				print(f"~\n{key}{value}\n# ", end = "")
			elif key != username and "@ " not in key and "send to firebase storage" not in key and print_data:
				print(f"~\n# {key}: {value}\n# ", end = "")
		print_data = True
	except TypeError:
		db.set({"Chat" : ""})

def last():
	global taken_files
	try:
		return taken_files[-1]
	except IndexError:
		print("@ Last is empty!")

def last_text():
	global taken_text_files
	try:
		return taken_text_files[-1]
	except IndexError:
		print("@ Last is empty!")
	

def list_files_in_storage():
	global storage
	file_list = []
	for file in storage.list_files():
		file_list.append(file.name)
	return file_list

def make_downloads_folder(path_to_downloads):
	try:
		os.mkdir(path_to_downloads)
	except FileExistsError:
		pass

def list_files_in_downloads(path_to_downloads):
	make_downloads_folder(path_to_downloads)
	return os.listdir(path_to_downloads)

def remove_downloads(path_to_downloads):
	make_downloads_folder(path_to_downloads)
	shutil.rmtree(path_to_downloads)
	print(f"@ Downloads removed")

def send_file(command):
	global storage, db
	path = command[command.find("\"") + 1:command.rfind("\"")]
	try:
		file_name = os.path.basename(path)
		if "." not in file_name:
			print("@ File must contain extension!")
		elif file_name in list_files_in_storage():
			msg = input("@ The firebase storage already has a file with this name. Replace the file? [Y/n]: ")
			if msg == "y":
				storage.child(file_name).put(path)
				db.child("Chat").push({f"@ {username} send to firebase storage " : file_name})
				print(f"File \"{file_name}\" sent")
			else:
				return
		else:
			storage.child(file_name).put(path)
			db.child("Chat").push({f"@ {username} send to firebase storage " : file_name})
			print(f"@ File \"{file_name}\" sent")
	except FileNotFoundError:
		print("@ File not found!")

def send_clipboard(path_to_downloads):
	global db
	make_downloads_folder(path_to_downloads)
	clipboard_file_name = "& clipboard.txt"
	with open(f"{path_to_downloads}\\{clipboard_file_name}", "w") as file:
		file.write(pyperclip.paste())
	storage.child(clipboard_file_name).put(f"{path_to_downloads}\\{clipboard_file_name}")
	db.child("Chat").push({f"@ {username} send to firebase storage " : "clipboard"})
	print("@ Clipboard sent")

def send_screenshot(path_to_downloads):
	global storage, db
	make_downloads_folder(path_to_downloads)
	screenshot_name = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S_screenshot.jpg")
	for i in range(10):
		print(f"@ {10 - i}")
		time.sleep(1)
	pyautogui.screenshot().save(f"{path_to_downloads}\\{screenshot_name}")
	storage.child(screenshot_name).put(f"{path_to_downloads}\\{screenshot_name}")
	db.child("Chat").push({f"@ {username} send to firebase storage " : screenshot_name})
	print("@ Screenshot ready and sent")
	return

def copy_file(file_name, path_to_downloads):
	global db
	make_downloads_folder(path_to_downloads)
	try:
		open(f"{path_to_downloads}\\{file_name[file_name.rfind('/') + 1:] if '/' in file_name else file_name}", "wb").write(requests.get(storage.child(file_name).get_url(None)).content)
		with open(f"{path_to_downloads}\\{file_name[file_name.rfind('/') + 1:] if '/' in file_name else file_name}", "r") as file:
			pyperclip.copy(file.read())
		print(f"@ File \"{file_name}\" copied file")
	except UnicodeDecodeError:
		print("@ Invalid file format!")
	except TypeError or FileNotFoundError:
		print("@ File not found!")

def copy_clipboard(path_to_downloads):
	global db
	make_downloads_folder(path_to_downloads)
	try:
		clipboard_file_name = "& clipboard.txt"
		open(f"{path_to_downloads}\\{clipboard_file_name}", "wb").write(requests.get(storage.child(clipboard_file_name).get_url(None)).content)
		with open(f"{path_to_downloads}\\{clipboard_file_name}", "r") as file:
			pyperclip.copy(file.read())
		print(f"@ Clipboard copied")
	except TypeError or FileNotFoundError:
		print("@ Clipboard not found!")

def open_file(file_name, path_to_downloads):
	global db
	make_downloads_folder(path_to_downloads)
	try:
		open(f"{path_to_downloads}\\{file_name[file_name.rfind('/') + 1:] if '/' in file_name else file_name}", "wb").write(requests.get(storage.child(file_name).get_url(None)).content)
		os.startfile(f"{path_to_downloads}\\{file_name[file_name.rfind('/') + 1:] if '/' in file_name else file_name}")
		print(f"@ File \"{file_name}\" open")
	except TypeError or FileNotFoundError:
		print("@ File not found!")

def open_clipboard(path_to_downloads):
	global db
	make_downloads_folder(path_to_downloads)
	try:
		clipboard_file_name = "& clipboard.txt"
		open(f"{path_to_downloads}\\{clipboard_file_name}", "wb").write(requests.get(storage.child(clipboard_file_name).get_url(None)).content)
		os.startfile(f"{path_to_downloads}\\{clipboard_file_name}")
		print(f"@ File \"{clipboard_file_name}\" open")
	except TypeError or FileNotFoundError:
		print("@ File not found!")

def type_file(file_name, path_to_downloads):
	make_downloads_folder(path_to_downloads)
	try:
		open(f"{path_to_downloads}\\{file_name[file_name.rfind('/') + 1:] if '/' in file_name else file_name}", "wb").write(requests.get(storage.child(file_name).get_url(None)).content)
		os.system(f"type \"{path_to_downloads}\\{file_name[file_name.rfind('/') + 1:] if '/' in file_name else file_name}\"")
		print()
	except TypeError or FileNotFoundError:
		print("@ File not found!")

def type_clipboard(path_to_downloads):
	make_downloads_folder(path_to_downloads)
	try:
		clipboard_file_name = "& clipboard.txt"
		open(f"{path_to_downloads}\\{clipboard_file_name}", "wb").write(requests.get(storage.child(clipboard_file_name).get_url(None)).content)
		os.system(f"type \"{path_to_downloads}\\{clipboard_file_name}\"")
		print()
	except TypeError or FileNotFoundError:
		print("@ File not found!")

def help_command():
	print("\n\t@ Pyrechat help command documentation\n\n\t& files in database     Prints list of files in firebase storage\n\t& files in downloads    Prints list of files in downloads folder\n\t& save path             Prints path to downloads folder\n\t& remove downloads      Remove downloads folder\n\t& send \"[path]\"         Sends a file to firebase storage\n\t& send clipboard        Write data from clipboard to txt file and send it to firebase storage\n\t& send screenshot       Takes a screenshot and send it to firebase storage\n\t& copy \"[path]\"         Download a file from firebase storage and copies it to clipboard\n\t& copy clipboard        Download a last release of \"& clipboard.txt\" from firebase storage and copies it to clipboard\n\t& copy last             Download a last received file from firebase storage and copies it to clipboard\n\t& open \"[path]\"         Download a file from firebase storage and opens it\n\t& open clipboard        Download a last release of \"& clipboard.txt\" from firebase storage and opens it\n\t& open last             Download a last received file from firebase storage and open it\n\t& type \"[path]\"         Download a file from firebase storage and prints it\n\t& type clipboard        Download a last release of \"& clipboard.txt\" from firebase storage and prints it\n\t& type last             Download a last received text file from firebase storage and prints it\n\t& help                  Prints pyrechat help documentation\n\t& exit                  Exits the pyrechat\n")

def main():
	global username, db
	path_to_downloads = os.path.expandvars("%USERPROFILE%\\Downloads\\Pyrechat")
	make_downloads_folder(path_to_downloads)
	print("@ Welcome to Pyrechat by MiZentUi!")
	while username == "":
		username = input("@ Write your name: ")
		if username == "":
			print("@ Name cannot be empty!")
	db.child("Chat").push({f"@ User {username} " : "connected"})
	db.child("Chat").stream(stream_handler)
	while True:
		msg = input("# ")
		if msg != "":
			if msg[0] == "&":
				if len(msg) > 1 and msg[1] == " ":
					if "& files" in msg:
						if msg == "& files in database" or msg == "& files in db":
							for file in list_files_in_storage():
								print(f"@ {file}")
						elif msg == "& files in downloads":
							for file in list_files_in_downloads(path_to_downloads):
								print(f"@ {file}")
						else:
							print("@ The command \"& files\" must contain the keywords: in database or in downloads!")
					elif "& save" in msg:
						if msg == "& save path":
							make_downloads_folder(path_to_downloads)
							print(f"@ {path_to_downloads}")
						else:
							print("@ Perhaps you meant \"& save path\"?")
					elif "& remove" in msg:
						if msg == "& remove downloads":
							remove_downloads(path_to_downloads)
						else:
							print("@ Perhaps you meant \"& remove downloads\"?")
					elif "& send" in msg:
						if "& send \"" in msg and msg[-1] == "\"" and msg.rfind("\"") != msg.find("\""):
							if msg == "& send \"\"":
								print("@ Path cannot be empty!")
							else:
								send_file(msg)
						elif msg == "& send clipboard":
							send_clipboard(path_to_downloads)
						elif msg == "& send screenshot":
							send_screenshot(path_to_downloads)
						else:
							print("@ The command \"& send\" must contain the path to the file in \"\" or keywords: clipboard or screenshot!")
					elif "& copy" in msg:
						if "& copy \"" in msg and msg[-1] == "\"" and msg.rfind("\"") != msg.find("\""):
							if msg == "& copy file \"\"":
								print("@ Path cannot be empty!")
							else:
								copy_file(msg[msg.find("\"") + 1:msg.rfind("\"")], path_to_downloads)
						elif msg == "& copy clipboard":
							copy_clipboard(path_to_downloads)
						elif msg == "& copy last":
							copy_file(last(), path_to_downloads)
						else:
							print("@ The command \"& copy \" must contain the path to the file from firebase storage in \"\" or keywords: clipboard or last!")
					elif "& open" in msg:
						if "& open \"" in msg and msg[-1] == "\""  and msg.rfind("\"") != msg.find("\""):
							if msg == "& open \"\"":
								print("@ Path cannot be empty!")
							else:
								open_file(msg[msg.find("\"") + 1:msg.rfind("\"")], path_to_downloads)
						elif msg == "& open clipboard":
							open_clipboard(path_to_downloads)
						elif msg == "& open last":
							open_file(last(), path_to_downloads)
						else:
							print("@ The command \"& open\" must contain the path to the file from firebase storage in \"\" or keywords: clipboard or last!")
					elif "& type" in msg:
						if "& type \"" in msg and msg[-1] == "\""  and msg.rfind("\"") != msg.find("\""):
							if msg == "& type \"\"":
								print("@ Path cannot be empty!")
							else:
								type_file(msg[msg.find("\"") + 1:msg.rfind("\"")], path_to_downloads)
						elif msg == "& type clipboard":
							type_clipboard(path_to_downloads)
						elif msg == "& type last":
							type_file(last_text(), path_to_downloads)
						else:
							print("@ The command \"& type\" must contain the path to the file from firebase storage in \"\" or keywords: clipboard or last!")
					elif msg == "& help":
						help_command()
					elif msg == "& exit":
						os.abort()
					else:
						print(f"@ Command \"{msg}\" not found!")
				else:
					print(f"@ Command \"{msg}\" not found!")
			else:
				db.child("Chat").push({username : msg})

if __name__ == "__main__":
	main()