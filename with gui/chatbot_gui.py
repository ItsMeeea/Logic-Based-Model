# integrated_family_chatbot_gui.py
import customtkinter as ctk
import threading
from datetime import datetime
import sys
import os

# Import your existing chatbot functions
try:
    from chatbot import parse_statement, parse_question, prolog
    print("✅ Successfully imported chatbot functions!")
except ImportError as e:
    print(f"❌ Error importing chatbot.py: {e}")
    print("Make sure chatbot.py is in the same directory as this GUI file")
    # Fallback functions for testing
    def parse_statement(prompt):
        return "OK! I learned something."
    def parse_question(prompt):
        return "No one found."

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

class FamilyChatbotGUI:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("Family Relationship Chatbot")
        self.root.geometry("800x900")
        self.root.minsize(600, 700)
        
        self.setup_layout()
        self.show_welcome_message()
        
    def setup_layout(self):
        """Create the GUI layout"""
        # Header with gradient effect
        self.header_frame = ctk.CTkFrame(self.root, height=90, corner_radius=0)
        self.header_frame.pack(fill="x", padx=0, pady=0)
        self.header_frame.pack_propagate(False)
        
        # Header content
        header_content = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        header_content.pack(expand=True, fill="both", padx=25, pady=15)
        
        # Title
        title_label = ctk.CTkLabel(header_content, 
                                  text="👨‍👩‍👧‍👦 Family Chatbot", 
                                  font=ctk.CTkFont(size=28, weight="bold"))
        title_label.pack(anchor="w")
        
        # Status indicator
        self.status_label = ctk.CTkLabel(header_content, 
                                        text="Ready to learn about your family", 
                                        font=ctk.CTkFont(size=14),
                                        text_color="gray")
        self.status_label.pack(anchor="w")
        
        # Chat area with custom styling
        self.chat_frame = ctk.CTkScrollableFrame(self.root, 
                                               corner_radius=10,
                                               scrollbar_button_color="gray70")
        self.chat_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Input area with modern styling
        self.input_frame = ctk.CTkFrame(self.root, height=120, corner_radius=15)
        self.input_frame.pack(fill="x", padx=20, pady=(0, 20))
        self.input_frame.pack_propagate(False)
        
        # Input field with placeholder
        self.text_input = ctk.CTkTextbox(self.input_frame, 
                                        height=60,
                                        font=ctk.CTkFont(size=14),
                                        corner_radius=10)
        self.text_input.pack(side="left", fill="both", expand=True, 
                           padx=(15, 10), pady=15)
        
        # Button container
        button_container = ctk.CTkFrame(self.input_frame, fg_color="transparent")
        button_container.pack(side="right", padx=(0, 15), pady=15)
        
        # Clear button
        self.clear_button = ctk.CTkButton(button_container, 
                                         text="Clear",
                                         font=ctk.CTkFont(size=12),
                                         width=60,
                                         height=25,
                                         fg_color="gray",
                                         hover_color="gray60",
                                         command=self.clear_chat)
        self.clear_button.pack(pady=(0, 5))
        
        # Send button
        self.send_button = ctk.CTkButton(button_container, 
                                        text="Send",
                                        font=ctk.CTkFont(size=14, weight="bold"),
                                        width=80,
                                        height=30,
                                        command=self.send_message)
        self.send_button.pack()
        
        # Bind events
        self.text_input.bind("<Return>", self.on_enter)
        self.text_input.bind("<Shift-Return>", self.on_shift_enter)
        self.text_input.bind("<KeyPress>", self.on_typing)
        self.text_input.focus()
        
        # Add placeholder text
        self.add_placeholder()
        
    def add_placeholder(self):
        """Add placeholder text to input field"""
        self.text_input.insert("1.0", "Type your message here... (e.g., 'John is the father of Mary')")
        self.text_input.bind("<FocusIn>", self.remove_placeholder)
        
    def remove_placeholder(self, event):
        """Remove placeholder text when focused"""
        current_text = self.text_input.get("1.0", "end-1c")
        if "Type your message here..." in current_text:
            self.text_input.delete("1.0", "end")
        self.text_input.unbind("<FocusIn>")
        
    def on_enter(self, event):
        """Handle Enter key press"""
        if not event.state & 0x1:  # If Shift is not pressed
            self.send_message()
            return "break"
        
    def on_shift_enter(self, event):
        """Handle Shift+Enter for new line"""
        return None
        
    def on_typing(self, event):
        """Update status when user is typing"""
        self.status_label.configure(text="Type your message...")
        
    def send_message(self):
        """Send user message and get bot response"""
        message = self.text_input.get("1.0", "end-1c").strip()
        if not message or "Type your message here..." in message:
            return
            
        # Clear input
        self.text_input.delete("1.0", "end")
        
        # Update status
        self.status_label.configure(text="Processing your message...")
        
        # Add user message
        self.add_user_message(message)
        
        # Show typing indicator
        typing_frame = self.add_typing_indicator()
        
        # Process bot response
        threading.Thread(target=self.process_bot_response, 
                        args=(message, typing_frame), daemon=True).start()
        
    def process_bot_response(self, message, typing_frame):
        """Process bot response in background thread"""
        try:
            import time
            time.sleep(0.8)  # Simulate processing
            
            # Handle exit commands
            if message.lower() in ["exit", "quit", "bye", "goodbye"]:
                response = "👋 Goodbye! Thanks for using the Family Chatbot!"
                self.root.after(0, lambda: self.replace_typing_with_response(typing_frame, response))
                self.root.after(2000, self.root.quit)
                return
                
            # Process with your chatbot logic
            if message.endswith("?"):
                response = parse_question(message)
            else:
                response = parse_statement(message)
                
            # Update status
            self.root.after(0, lambda: self.status_label.configure(text="Ready to learn about your family"))
            
            # Replace typing indicator with response
            self.root.after(0, lambda: self.replace_typing_with_response(typing_frame, response))
            
        except Exception as e:
            error_msg = f"❌ Sorry, I encountered an error: {str(e)}"
            self.root.after(0, lambda: self.status_label.configure(text="Error occurred"))
            self.root.after(0, lambda: self.replace_typing_with_response(typing_frame, error_msg))
            
    def show_welcome_message(self):
        """Show welcome message"""
        welcome_text = """👋 Welcome to the Family Chatbot!

I can help you build and explore family relationships. Here's what you can do:

📝 **Tell me about relationships:**
• "John is the father of Mary"
• "Alice and Bob are siblings"
• "Sarah is the grandmother of Tom"

❓ **Ask me questions:**
• "Who are the children of John?"
• "Is Mary the daughter of John?"
• "Are Alice and Bob siblings?"

🔍 **I can handle typos and variations:**
• "gradfather" → "grandfather"
• "childre" → "children"

Let's start building your family tree! 🌳"""
        
        self.add_bot_message(welcome_text)
        
    def add_user_message(self, message):
        """Add user message to chat"""
        message_container = ctk.CTkFrame(self.chat_frame, fg_color="transparent")
        message_container.pack(fill="x", pady=(5, 5))
        
        # User message frame
        user_frame = ctk.CTkFrame(message_container, corner_radius=15)
        user_frame.pack(anchor="e", padx=(100, 0))
        
        message_label = ctk.CTkLabel(user_frame,
                                   text=message,
                                   font=ctk.CTkFont(size=13),
                                   wraplength=300,
                                   justify="left")
        message_label.pack(padx=15, pady=10)
        
        # Timestamp
        timestamp = ctk.CTkLabel(message_container,
                               text=datetime.now().strftime("%H:%M"),
                               font=ctk.CTkFont(size=10),
                               text_color="gray")
        timestamp.pack(anchor="e", pady=(2, 0))
        
        self.scroll_to_bottom()
        
    def add_bot_message(self, message):
        """Add bot message to chat"""
        message_container = ctk.CTkFrame(self.chat_frame, fg_color="transparent")
        message_container.pack(fill="x", pady=(5, 5))
        
        # Bot container
        bot_container = ctk.CTkFrame(message_container, fg_color="transparent")
        bot_container.pack(anchor="w", fill="x")
        
        # Avatar
        avatar_frame = ctk.CTkFrame(bot_container, width=40, height=40, corner_radius=20)
        avatar_frame.pack(side="left", anchor="n", padx=(0, 10))
        avatar_frame.pack_propagate(False)
        
        avatar_label = ctk.CTkLabel(avatar_frame, text="🤖", font=ctk.CTkFont(size=20))
        avatar_label.pack(expand=True)
        
        # Message bubble
        bot_frame = ctk.CTkFrame(bot_container, corner_radius=15, fg_color="gray90")
        bot_frame.pack(side="left", anchor="n", padx=(0, 100))
        
        message_label = ctk.CTkLabel(bot_frame,
                                   text=message,
                                   font=ctk.CTkFont(size=13),
                                   wraplength=350,
                                   justify="left",
                                   text_color="black")
        message_label.pack(padx=15, pady=10)
        
        # Timestamp
        timestamp = ctk.CTkLabel(message_container,
                               text=datetime.now().strftime("%H:%M"),
                               font=ctk.CTkFont(size=10),
                               text_color="gray")
        timestamp.pack(anchor="w", pady=(2, 0))
        
        self.scroll_to_bottom()
        
    def add_typing_indicator(self):
        """Add typing indicator"""
        message_container = ctk.CTkFrame(self.chat_frame, fg_color="transparent")
        message_container.pack(fill="x", pady=(5, 5))
        
        bot_container = ctk.CTkFrame(message_container, fg_color="transparent")
        bot_container.pack(anchor="w", fill="x")
        
        # Avatar
        avatar_frame = ctk.CTkFrame(bot_container, width=40, height=40, corner_radius=20)
        avatar_frame.pack(side="left", anchor="n", padx=(0, 10))
        avatar_frame.pack_propagate(False)
        
        avatar_label = ctk.CTkLabel(avatar_frame, text="🤖", font=ctk.CTkFont(size=20))
        avatar_label.pack(expand=True)
        
        # Typing indicator with animation
        typing_frame = ctk.CTkFrame(bot_container, corner_radius=15, fg_color="gray90")
        typing_frame.pack(side="left", anchor="n")
        
        typing_label = ctk.CTkLabel(typing_frame,
                                  text="🤔 Bot is thinking...",
                                  font=ctk.CTkFont(size=13, slant="italic"),
                                  text_color="gray40")
        typing_label.pack(padx=15, pady=10)
        
        self.scroll_to_bottom()
        return message_container
        
    def replace_typing_with_response(self, typing_frame, response):
        """Replace typing indicator with actual response"""
        typing_frame.destroy()
        self.add_bot_message(response)
        
    def clear_chat(self):
        """Clear all chat messages"""
        for widget in self.chat_frame.winfo_children():
            widget.destroy()
        self.show_welcome_message()
        self.status_label.configure(text="Chat cleared - Ready to start fresh!")
        
    def scroll_to_bottom(self):
        """Scroll to bottom of chat"""
        self.root.after(10, lambda: self.chat_frame._parent_canvas.yview_moveto(1.0))
        
    def run(self):
        """Start the application"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()
        
    def on_closing(self):
        """Handle window closing"""
        self.root.quit()
        self.root.destroy()

def main():
    """Run the family chatbot GUI"""
    print("🚀 Starting Family Chatbot GUI...")
    app = FamilyChatbotGUI()
    app.run()

if __name__ == "__main__":
    main()
