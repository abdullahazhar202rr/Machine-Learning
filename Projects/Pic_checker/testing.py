# main.py - GUI application for picture checker

import sys
import os

# Add scripts directory to Python path
scripts_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scripts')
sys.path.insert(0, scripts_path)

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import cv2
from PIL import Image, ImageTk
import threading
from checker import PictureChecker
from config import MSG_SUCCESS

class PictureCheckerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Professional Picture Checker")
        self.root.geometry("1000x700")
        
        self.checker = PictureChecker()
        self.camera = None
        self.camera_running = False
        self.current_frame = None
        
        # Create logs directory if it doesn't exist
        os.makedirs("logs", exist_ok=True)
        os.makedirs("data/input", exist_ok=True)
        os.makedirs("data/output", exist_ok=True)
        
        self.setup_ui()
    
    def setup_ui(self):
        # Title
        title_label = tk.Label(self.root, text="Professional Picture Checker", 
                               font=("Arial", 20, "bold"), pady=10)
        title_label.pack()
        
        # Subtitle
        subtitle = tk.Label(self.root, 
                           text="Validate your professional photo: one person, front-facing, closed mouth, no tilt",
                           font=("Arial", 10), fg="gray")
        subtitle.pack()
        
        # Mode selection frame
        mode_frame = tk.Frame(self.root, pady=20)
        mode_frame.pack()
        
        tk.Label(mode_frame, text="Choose Mode:", font=("Arial", 12, "bold")).pack()
        
        button_frame = tk.Frame(mode_frame)
        button_frame.pack(pady=10)
        
        self.camera_btn = tk.Button(button_frame, text="📷 Use Camera (Live Guidance)", 
                                     font=("Arial", 12), bg="#4CAF50", fg="white",
                                     padx=20, pady=10, command=self.start_camera_mode)
        self.camera_btn.grid(row=0, column=0, padx=10)
        
        self.upload_btn = tk.Button(button_frame, text="🖼️ Upload Picture", 
                                     font=("Arial", 12), bg="#2196F3", fg="white",
                                     padx=20, pady=10, command=self.upload_picture_mode)
        self.upload_btn.grid(row=0, column=1, padx=10)
        
        # Video/Image display frame
        self.display_frame = tk.Frame(self.root, bg="black", width=640, height=480)
        self.display_frame.pack(pady=20)
        self.display_frame.pack_propagate(False)
        
        self.video_label = tk.Label(self.display_frame, bg="black")
        self.video_label.pack(expand=True)
        
        # Control buttons frame
        self.control_frame = tk.Frame(self.root)
        self.control_frame.pack(pady=10)
        
        # Status label
        self.status_label = tk.Label(self.root, text="", font=("Arial", 11), 
                                     fg="blue", wraplength=800)
        self.status_label.pack(pady=10)
        
        # Instructions
        instructions = """
        Camera Mode: Get real-time feedback while adjusting your pose
        Upload Mode: Validate an existing picture file
        
        Requirements:
        ✓ Exactly one person in frame
        ✓ Face looking straight at camera
        ✓ Head not tilted left or right
        ✓ Mouth closed
        ✓ Good lighting and clear image
        """
        
        instructions_label = tk.Label(self.root, text=instructions, 
                                     font=("Arial", 9), justify=tk.LEFT, fg="gray")
        instructions_label.pack(pady=10)
    
    def start_camera_mode(self):
        """Start camera with live validation"""
        if self.camera_running:
            self.stop_camera()
            return
        
        self.camera = cv2.VideoCapture(0)
        if not self.camera.isOpened():
            messagebox.showerror("Error", "Could not access camera")
            return
        
        self.camera_running = True
        self.camera_btn.config(text="⏹️ Stop Camera", bg="#f44336")
        self.upload_btn.config(state=tk.DISABLED)
        
        # Clear control frame and add capture button
        for widget in self.control_frame.winfo_children():
            widget.destroy()
        
        self.capture_btn = tk.Button(self.control_frame, text="📸 Capture Picture", 
                                      font=("Arial", 12), bg="#FF9800", fg="white",
                                      padx=20, pady=10, command=self.capture_picture)
        self.capture_btn.pack()
        
        self.status_label.config(text="Camera active - Adjust your pose based on guidance", fg="blue")
        
        # Start video thread
        self.video_thread = threading.Thread(target=self.process_camera_feed, daemon=True)
        self.video_thread.start()
    
    def process_camera_feed(self):
        """Process camera feed with real-time validation"""
        while self.camera_running:
            ret, frame = self.camera.read()
            if not ret:
                break
            
            # Flip frame horizontally for mirror effect
            frame = cv2.flip(frame, 1)
            
            # Validate frame
            is_valid, issues, annotated_frame = self.checker.validate_image(frame, draw_feedback=True)
            
            self.current_frame = frame.copy()  # Store original frame
            
            # Convert for Tkinter display
            frame_rgb = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
            frame_pil = Image.fromarray(frame_rgb)
            frame_pil = frame_pil.resize((640, 480), Image.Resampling.LANCZOS)
            frame_tk = ImageTk.PhotoImage(frame_pil)
            
            # Update display
            self.video_label.config(image=frame_tk)
            self.video_label.image = frame_tk
    
    def capture_picture(self):
        """Capture and save the current frame"""
        if self.current_frame is None:
            messagebox.showwarning("Warning", "No frame to capture")
            return
        
        # Validate the captured frame
        is_valid, issues, annotated_frame = self.checker.validate_image(self.current_frame, draw_feedback=False)
        
        if is_valid:
            # Save to output folder
            timestamp = cv2.getTickCount()
            filename = f"data/output/approved_{timestamp}.jpg"
            cv2.imwrite(filename, self.current_frame)
            
            messagebox.showinfo("Success", f"✅ Picture approved and saved!\n\n{filename}")
            self.status_label.config(text=f"✅ Picture saved: {filename}", fg="green")
        else:
            messagebox.showwarning("Not Approved", 
                                  f"❌ Picture does not meet requirements:\n\n" + 
                                  "\n".join(f"• {issue}" for issue in issues))
            self.status_label.config(text="❌ Picture not approved - fix issues and try again", fg="red")
    
    def stop_camera(self):
        """Stop camera feed"""
        self.camera_running = False
        if self.camera:
            self.camera.release()
        
        self.camera_btn.config(text="📷 Use Camera (Live Guidance)", bg="#4CAF50")
        self.upload_btn.config(state=tk.NORMAL)
        
        # Clear display
        self.video_label.config(image="")
        self.status_label.config(text="Camera stopped", fg="gray")
        
        # Clear control buttons
        for widget in self.control_frame.winfo_children():
            widget.destroy()
    
    def upload_picture_mode(self):
        """Upload and validate a picture file"""
        file_path = filedialog.askopenfilename(
            title="Select Picture",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp"), ("All files", "*.*")]
        )
        
        if not file_path:
            return
        
        # Load and display image
        image = cv2.imread(file_path)
        if image is None:
            messagebox.showerror("Error", "Could not load image")
            return
        
        # Validate image
        is_valid, issues, annotated_frame = self.checker.validate_image(image, draw_feedback=True)
        
        # Display result
        frame_rgb = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
        frame_pil = Image.fromarray(frame_rgb)
        
        # Resize to fit display
        display_width = 640
        aspect_ratio = frame_pil.height / frame_pil.width
        display_height = int(display_width * aspect_ratio)
        if display_height > 480:
            display_height = 480
            display_width = int(display_height / aspect_ratio)
        
        frame_pil = frame_pil.resize((display_width, display_height), Image.Resampling.LANCZOS)
        frame_tk = ImageTk.PhotoImage(frame_pil)
        
        self.video_label.config(image=frame_tk)
        self.video_label.image = frame_tk
        
        # Update status
        if is_valid:
            self.status_label.config(text=f"✅ {MSG_SUCCESS}", fg="green")
            
            # Ask to save
            if messagebox.askyesno("Approved", "Picture approved! Save to output folder?"):
                filename = os.path.basename(file_path)
                output_path = f"data/output/approved_{filename}"
                cv2.imwrite(output_path, image)
                messagebox.showinfo("Saved", f"Picture saved to: {output_path}")
        else:
            self.status_label.config(
                text=f"❌ Picture not approved: {', '.join(issues)}", 
                fg="red"
            )
            messagebox.showwarning("Not Approved", 
                                  "Picture does not meet requirements:\n\n" + 
                                  "\n".join(f"• {issue}" for issue in issues))
        
        # Add buttons to try again or upload another
        for widget in self.control_frame.winfo_children():
            widget.destroy()
        
        tk.Button(self.control_frame, text="📤 Upload Another", 
                 font=("Arial", 11), bg="#2196F3", fg="white",
                 padx=15, pady=8, command=self.upload_picture_mode).pack()
    
    def on_closing(self):
        """Clean up when closing the application"""
        self.camera_running = False
        if self.camera:
            self.camera.release()
        self.checker.close()
        self.root.destroy()

def main():
    root = tk.Tk()
    app = PictureCheckerGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()