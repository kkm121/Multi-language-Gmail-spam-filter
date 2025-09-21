from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB
import joblib
import os
import tkinter as tk
from tkinter import ttk, messagebox
from googletrans import Translator
import pygame
import threading
class InitialScreen:
    def __init__(self, master):
        self.master = master
        self.master.title("Select Option")
        self.master.geometry("400x200")
        self.label = tk.Label(master, text="Select an option:", font=("TkDefaultFont", 16))
        self.label.pack(pady=20)
        self.gui_button = tk.Button(master, text="GUI Spam Filter", command=self.run_gui_spam_filter, font=("TkDefaultFont", 14))
        self.gui_button.pack(pady=10)
        self.gmail_button = tk.Button(master, text="Gmail Spam Filter", command=self.run_gmail_spam_filter_gui, font=("TkDefaultFont", 14))
        self.gmail_button.pack(pady=10)
    def run_gui_spam_filter(self):
        self.master.destroy()
        root = tk.Tk()
        app = SpamFilterApp(root)
        root.mainloop()
    def run_gmail_spam_filter_gui(self):
        self.master.destroy()
        gmail_service = create_gmail_service()
        classifier = joblib.load('classifier_model.joblib')
        vectorizer = joblib.load('vectorizer.joblib') 
        get_and_classify_emails_gui(gmail_service, classifier, vectorizer, num_messages=10)
class SpamFilterApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Spam Filter App")
        self.master.geometry("800x600")
        bg_image = tk.PhotoImage(file="bg_image.png")  # Replace with actual path
        bg_label = tk.Label(master, image=bg_image)
        bg_label.place(relwidth=1, relheight=1)
        self.master.bg_image = bg_image
        self.label = tk.Label(master, text="Enter a message:", font=("TkDefaultFont", 16), bg="#ffffff")
        self.label.pack(pady=20)
        self.text_entry = tk.Entry(master, width=50, font=("TkDefaultFont", 14))
        self.text_entry.pack(pady=10)
        most_spoken_languages = ["普通话 中文", "español", "English", "हिन्दी", "عربي", "বাংলা", "Português", "Русский язык", "اردو", "Bahasa Indonesia",
                                "français", "بهاس ملايو", "Deutsch", "日本語 ", "తెలుగు", "Tiếng Việt", "한국인", "தமிழ்", "मराठी", "Türkçe"]
        self.language_var = tk.StringVar(value="English")
        self.language_menu = ttk.Combobox(master, textvariable=self.language_var, values=most_spoken_languages)
        self.language_menu.pack(pady=10)
        self.classifier = joblib.load('classifier_model.joblib')  
        self.vectorizer = joblib.load('vectorizer.joblib')
        self.classify_button = tk.Button(master, text="Classify", command=self.classify_message, font=("TkDefaultFont", 12))
        self.classify_button.pack(pady=5)
        ttk.Separator(master, orient='horizontal').pack(fill='x', pady=10)
        self.result_label = tk.Label(master, text="", font=("TkDefaultFont", 16), wraplength=300)
        self.result_label.pack(pady=10)
        self.verify_translation_button = tk.Button(master, text="Verify Translation", command=self.verify_translation, font=("TkDefaultFont", 12))
        self.verify_translation_button.pack(pady=5)
        self.exit_button = tk.Button(master, text="Exit", command=self.exit_app, font=("TkDefaultFont", 14))
        self.exit_button.pack(side=tk.RIGHT, padx=10, pady=10)
        pygame.init()
        self.spam_detected_sound = pygame.mixer.Sound("spam_detected.wav")
        self.not_spam_sound = pygame.mixer.Sound("not_spam.wav")
    def classify_message(self):
        try:
            input_text = self.text_entry.get()
            if not input_text:
                self.result_label.config(text="")
                return
            if self.language_var.get() != "English":
                input_text = self.translate_to_english(input_text)
            input_vectorized = self.vectorizer.transform([input_text])
            prediction = self.classifier.predict(input_vectorized)
            if prediction[0] == 0:
                self.result_label.config(text="This message is not spam.", fg="green")
                self.not_spam_sound.play()
            else:
                self.result_label.config(text="Warning! This message may be spam.", fg="red")
                self.spam_detected_sound.play()
        except Exception as e:
            import traceback
            traceback.print_exc()
            messagebox.showerror("Error", "An error occurred: {}".format(str(e)))
    def translate_to_english(self, text):
        language_mapping = {
            "普通话 中文": "zh-CN",
            "español": "es",
            "English": "en",
            "हिन्दी": "hi",
            "عربي": "ar",
            "বাংলা": "bn",
            "Português": "pt",
            "Русский язык": "ru",
            "اردو": "ur",
            "Bahasa Indonesia": "id",
            "français": "fr",
            "بهاس ملايو": "ms",
            "Deutsch": "de",
            "日本語 ": "ja",
            "తెలుగు": "te",
            "Tiếng Việt": "vi",
            "한국인": "ko",
            "தமிழ்": "ta",
            "मराठी": "mr",
            "Türkçe": "tr"
        }
        if self.language_var.get() != "English":
            translator = Translator()
            translated_text = translator.translate(text, src=language_mapping.get(self.language_var.get()), dest="en").text
            return translated_text
        else:
            return text
    def verify_translation(self):
        try:
            input_text = self.text_entry.get()
            if not input_text:
                messagebox.showwarning("Warning", "Please enter a message.")
                return
            if self.language_var.get() != "English":
                translated_text = self.translate_to_english(input_text)
                VerificationPopup(tk.Toplevel(self.master), input_text, translated_text)
            else:
                messagebox.showinfo("Translation Verification", "Original Text: {}\nTranslated Text: {}".format(input_text, input_text))
        except Exception as e:
            import traceback
            traceback.print_exc()
            messagebox.showerror("Error", "An error occurred: {}".format(str(e)))
    def exit_app(self):
        pygame.mixer.quit()
        self.master.destroy()
class VerificationPopup:
    def __init__(self, master, original_text, translated_text):
        self.master = master
        self.master.title("Translation Verification")
        self.master.geometry("400x200")
        self.original_label = tk.Label(master, text="Original Text: {}".format(original_text), font=("TkDefaultFont", 14))
        self.original_label.pack(pady=10)
        self.translated_label = tk.Label(master, text="Translated Text: {}".format(translated_text), font=("TkDefaultFont", 14))
        self.translated_label.pack(pady=10)
        self.ok_button = tk.Button(master, text="OK", command=self.close_popup, font=("TkDefaultFont", 14))
        self.ok_button.pack(pady=10)
    def close_popup(self):
        self.master.destroy()
def create_gmail_service():
    credentials_path = r"C:\Users\Muthukumaran\Desktop\cs_project\client_secret_294449253405-f0grrnc074b1ggi22lukfk74tqa070j6.apps.googleusercontent.com.json"
    flow = InstalledAppFlow.from_client_secrets_file(credentials_path, ['https://www.googleapis.com/auth/gmail.modify'])
    creds = None
    token_path = 'token.json'
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            creds = flow.run_local_server(port=0)
        with open(token_path, 'w') as token:
            token.write(creds.to_json())
    service = build('gmail', 'v1', credentials=creds)
    return service
def classify_message(classifier, vectorizer, message_text):
    input_vectorized = vectorizer.transform([message_text])
    prediction = classifier.predict(input_vectorized)
    if prediction[0] == 0:
        return "Not spam"
    else:
        return "Spam"
def move_to_spam_folder(service, user_id='me', message_id=''):
    try:
        service.users().messages().modify(
            userId=user_id,
            id=message_id,
            body={'removeLabelIds': ['INBOX'], 'addLabelIds': ['SPAM']}
        ).execute()
        print(f"Moved message {message_id} to Spam folder.")
    except Exception as e:
        print(f"Error moving message {message_id} to Spam folder: {e}")
def get_and_classify_emails_gui(service, classifier, vectorizer, user_id='me', num_messages=10):
    response = service.users().messages().list(userId=user_id, maxResults=num_messages).execute()
    messages = response.get('messages', [])
    if not messages:
        print("No messages found.")
        return
    result_window = tk.Tk()
    result_window.title("Gmail Spam Filter Results")
    result_window.geometry("800x600")
    result_label = tk.Label(result_window, text="Gmail Spam Filter Results", font=("TkDefaultFont", 20))
    result_label.pack(pady=10)
    progress_var = tk.DoubleVar()
    progress_bar = ttk.Progressbar(result_window, variable=progress_var, maximum=len(messages))
    progress_bar.pack(fill="x", pady=10)
    result_text = tk.Text(result_window, wrap=tk.WORD, font=("TkDefaultFont", 14), state=tk.NORMAL)  # Use Text widget
    result_text.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
    def classify_and_update_gui(msg, progress_var):
        message = service.users().messages().get(userId=user_id, id=msg['id']).execute()
        msg_text = message['snippet']
        prediction = classify_message(classifier, vectorizer, msg_text)
        msg_result_text = f"Message {msg['id']}: {prediction} - {msg_text}\n\n"
        result_text.insert(tk.END, msg_result_text)
        result_text.see(tk.END)  # Auto-scroll to the end
        progress_var.set(progress_var.get() + 1)
        result_window.update_idletasks()
        if prediction == "Spam":
            move_to_spam_folder(service, user_id, msg['id'])
    def process_messages():
        for i, msg in enumerate(messages):
            classify_and_update_gui(msg, progress_var)
    thread = threading.Thread(target=process_messages)
    thread.start()
    result_window.mainloop()
if __name__ == "__main__":
    root = tk.Tk()
    initial_screen = InitialScreen(root)
    root.mainloop()
