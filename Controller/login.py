# ui/login.py
class LoginWindow:
    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        conn = sqlite3.connect("store_system.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM SystemUser WHERE username=? AND password=?", (username, password))
        user = cursor.fetchone()
        conn.close()

        if user:
            messagebox.showinfo("Success", f"Welcome, {username}!")
            self.frame.destroy()
            MainMenu(self.master, username)
        else:
            messagebox.showerror("Error", "Invalid username or password.")