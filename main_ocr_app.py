import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import pytesseract
import os
import threading

ctk.set_appearance_mode("dark")  # Modes: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue", "dark-blue", "green"


class UpperFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, corner_radius=10)
        self.master = master
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)

        self.fileselector_lbl = ctk.CTkLabel(self, text="Select Folder", anchor="w", font=("Arial", 14, "bold"))
        self.fileselector_lbl.grid(row=0, column=0, sticky="nesw", padx=10, pady=(5, 2))

        self.fileselector = ctk.CTkButton(self, text="Select Folder", fg_color="#3b8ed0", text_color="white", command=self.select_folder)
        self.fileselector.grid(row=1, column=0, sticky="nesw", padx=10, pady=5)

        self.clear_btn = ctk.CTkButton(self, text="Clear", fg_color="red", text_color="white", command=self.clear_results)
        self.clear_btn.grid(row=1, column=1, sticky="nesw", padx=10, pady=5)

        self.search_lbl = ctk.CTkLabel(self, text="Enter Words", anchor="w", font=("Arial", 14, "bold"))
        self.search_lbl.grid(row=2, column=0, sticky="nesw", padx=10, pady=(10, 2))
            
        self.search = ctk.CTkEntry(self, placeholder_text="Enter words", font=("Arial", 12))
        self.search.grid(row=3, column=0, sticky="nesw", padx=10, pady=5)

        self.search_btn = ctk.CTkButton(self, text="Search", fg_color="#1e81b0", text_color="white", command=self.start_search)
        self.search_btn.grid(row=3, column=1, sticky="nesw", padx=10, pady=5)
        
    def select_folder(self):
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.fileselector.configure(text=f"Selected Folder: {folder_path}")
            self.folder_path = folder_path
    
    def start_search(self):
        self.master.clear_bottom_frame()
        self.loader = LoaderFrame(self.master.bottomframe)
        self.loader.pack(fill="both", expand=True, padx=10, pady=10)
        
        threading.Thread(target=self.search_word, args=(self.loader, self.on_search_complete)).start()
        
        
    def on_search_complete(self, results, loader):
        loader.destroy()
        self.master.show_image(results)

    def search_word(self, loader, callback):
        if not hasattr(self, 'folder_path') or not self.folder_path:
            messagebox.showerror("Error", "Please select a folder.")
            self.master.loader.stop_loader()
            return
        
        words_input = self.search.get().strip()
        if not words_input:
            messagebox.showerror("Error", "Please enter some words to search.")
            self.master.loader.stop_loader()
            return
        
        words = [word.strip() for word in words_input.split(",") if word.strip()]
        if not words:
            messagebox.showerror("Error", "Please enter valid words.")
            self.master.loader.stop_loader()
            return
        
        results = self.find_words_in_folder(self.folder_path, words)
        
        self.master.after(0, callback, results, loader)

    def find_words_in_image(self, image_path, words_to_find):
        image = Image.open(image_path)
        extracted_text = pytesseract.image_to_string(image)
        lines = extracted_text.split('\n')
        
        words_found = []
        lines_with_words = []
        
        for line in lines:
            for word in words_to_find:
                if word.lower() in line.lower():
                    if word not in words_found:
                        words_found.append(word)
                    lines_with_words.append(line)
                    break
        result = {
            'Found': bool(words_found),
            'Image Path': image_path,
            'Words Found': words_found,
            'Lines with Words': lines_with_words
        }
        return result

    def find_words_in_folder(self, folder_path, words_to_find):
        results = []
        supported_formats = ('.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.gif')
        for filename in os.listdir(folder_path):
            if filename.lower().endswith(supported_formats):
                image_path = os.path.join(folder_path, filename)
                result = self.find_words_in_image(image_path, words_to_find)
                if result['Found']:
                    result['Image Name'] = filename
                    results.append(result)
        return results
    
    def clear_results(self):
        self.search.delete(0, 'end')
        self.master.clear_bottom_frame()

class ResultFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, corner_radius=10)
        self.master = master
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=3)

        self.imgcontainerframe = ctk.CTkFrame(self)
        self.imgcontainerframe.grid(row=0, column=0, sticky="nesw", padx=10, pady=5)

        self.img = ctk.CTkLabel(self.imgcontainerframe, text="Image Preview", font=("Arial", 12, "italic"))
        self.img.pack(side="top", fill="both", expand=True, padx=10, pady=10)

        self.detailframe = ctk.CTkScrollableFrame(self)
        self.detailframe.grid(row=0, column=1, sticky="nesw", padx=10, pady=5)

        self.image_name_lbl = ctk.CTkLabel(self.detailframe, text="Image Name", anchor="w", font=("Arial", 12, "bold"))
        self.image_name_lbl.pack(fill="x", padx=10, pady=5)
        
        self.image_path_lbl = ctk.CTkLabel(self.detailframe, text="Image Path", anchor="w", font=("Arial", 12))
        self.image_path_lbl.pack(fill="x", padx=10, pady=5)
        
        self.word_lbl = ctk.CTkLabel(self.detailframe, text="Word", anchor="w", font=("Arial", 12))
        self.word_lbl.pack(fill="x", padx=10, pady=5)
        
        self.context_lbl = ctk.CTkLabel(self.detailframe, text="Context", anchor="w", font=("Arial", 12))
        self.context_lbl.pack(fill="x", padx=10, pady=5)
    
    def open_image(self, image_path):
        os.startfile(image_path)

class LoaderFrame(ctk.CTkFrame):
    path = "loader.png"
    angle = 0
    
    def __init__(self, master):
        super().__init__(master, corner_radius=10)
        
        self.master = master
        self.original_image = Image.open(self.path)
        self.ctk_image = ctk.CTkImage(self.original_image, size=(100, 100))
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
    
        self.lbl = ctk.CTkLabel(self, text="", height=100, width=100, image=self.ctk_image)
        self.lbl.grid(row=0, column=0, pady=10, padx=20, sticky="nsew")
        self.loader()

    def loader(self):
        rotated_image = self.original_image.rotate(self.angle)
        self.ctk_image = ctk.CTkImage(rotated_image, size=(100, 100))
        self.lbl.configure(image=self.ctk_image)
        self.angle += 10  # Adjust the speed of rotation
        self.after(50, self.loader)  # Adjust the delay


class OCR_App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("OCR App")
        self.geometry("700x600")
        self.minsize(700, 700)

        # search and file chooser frame
        self.topframe = UpperFrame(self)
        self.topframe.pack(fill="both", padx=10, pady=10)

        # Bottom frame for results
        self.bottomframe = ctk.CTkScrollableFrame(self, corner_radius=10)
        self.bottomframe.pack(fill="both", expand=True, padx=10, pady=10)

    def show_image(self, results):
        for result in results:
            result_frame = ResultFrame(self.bottomframe)
            result_frame.pack(fill="both", padx=10, pady=10)
            
            img = Image.open(result['Image Path'])
            img = img.resize((150, 150))
            photo = ImageTk.PhotoImage(img)

            # Set image to the label
            result_frame.img.configure(image=photo)
            result_frame.img.configure(text="")
            result_frame.img.image = photo
            result_frame.img.bind("<Button-1>", lambda e, path=result['Image Path']: result_frame.open_image(path))

            # Set data for the ResultFrame
            result_frame.image_name_lbl.configure(text=f"Image Name: {result['Image Name']}")
            result_frame.image_path_lbl.configure(text=f"Image Path: {result['Image Path']}")
            result_frame.word_lbl.configure(text=f"Word: {', '.join(result['Words Found'])}")
            result_frame.context_lbl.configure(text=f"Context: {' '.join(result['Lines with Words'])}")

    def clear_bottom_frame(self):
        for widget in self.bottomframe.winfo_children():
            widget.destroy()

if __name__ == '__main__':
    app = OCR_App()
    app.mainloop()
