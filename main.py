import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import cv2
import os
from pathlib import Path
import threading
from datetime import datetime, timedelta

class VideoFrameExtractor:
    def __init__(self, root: tk.Tk):
        
        self.root = root
        self.root.title("Video Frame Extractor")
        self.root.geometry("800x700")
        
        # Set window icon - using absolute path
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            icon_path = os.path.join(current_dir, "ico.ico")
            if os.path.exists(icon_path):
                self.root.iconbitmap(default=icon_path)
            else:
                print(f"Icon not found at: {icon_path}")
        except Exception as e:
            print(f"Error setting icon: {str(e)}")
        
        # Instance variables
        self.video_path = None
        self.save_directory = None
        self.extraction_thread = None
        self.is_extracting = False
        self.video_info = {}
        
        self.create_widgets()

    def create_widgets(self):
        """Create and arrange all GUI widgets."""
        # Main container
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky="nsew")
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # Title
        ttk.Label(
            main_frame, 
            text="Video Frame Extractor", 
            font=('Helvetica', 16, 'bold')
        ).grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Video Selection Section
        video_frame = ttk.LabelFrame(main_frame, text="Video Selection", padding="10")
        video_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 15))
        
        ttk.Label(video_frame, text="Video File:").grid(row=0, column=0, sticky="w", pady=5)
        
        self.video_path_var = tk.StringVar()
        video_entry = ttk.Entry(video_frame, textvariable=self.video_path_var)
        video_entry.grid(row=0, column=1, sticky="ew", padx=5)
        
        ttk.Button(
            video_frame,
            text="Browse",
            command=self.select_video,
            width=15
        ).grid(row=0, column=2, padx=(5, 0))
        
        # Output Directory Section
        output_frame = ttk.LabelFrame(main_frame, text="Output Settings", padding="10")
        output_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 15))
        
        self.same_dir_var = tk.BooleanVar()
        ttk.Checkbutton(
            output_frame,
            text="Save in the same directory as video",
            variable=self.same_dir_var,
            command=self.toggle_output_directory
        ).grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 5))
        
        ttk.Label(output_frame, text="Output Directory:").grid(
            row=1, column=0, sticky="w", pady=5
        )
        
        self.save_path_var = tk.StringVar()
        self.output_entry = ttk.Entry(output_frame, textvariable=self.save_path_var)
        self.output_entry.grid(row=1, column=1, sticky="ew", padx=5)
        
        self.browse_output_btn = ttk.Button(
            output_frame,
            text="Browse",
            command=self.select_save_directory,
            width=15
        )
        self.browse_output_btn.grid(row=1, column=2, padx=(5, 0))
        
        # Extraction Settings
        settings_frame = ttk.LabelFrame(main_frame, text="Extraction Settings", padding="10")
        settings_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0, 15))
        
        ttk.Label(settings_frame, text="Number of Frames:").grid(
            row=0, column=0, sticky="w", padx=(0, 10)
        )
        self.frame_count_var = tk.StringVar(value="10")
        ttk.Entry(
            settings_frame,
            textvariable=self.frame_count_var,
            width=10
        ).grid(row=0, column=1, sticky="w")
        
        ttk.Label(settings_frame, text="Image Format:").grid(
            row=0, column=2, sticky="w", padx=(20, 10)
        )
        self.format_var = tk.StringVar(value="jpg")
        ttk.Combobox(
            settings_frame,
            textvariable=self.format_var,
            values=["jpg", "png"],
            width=5,
            state="readonly"
        ).grid(row=0, column=3, sticky="w")
        
        # Video Information
        info_frame = ttk.LabelFrame(main_frame, text="Video Information", padding="10")
        info_frame.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(0, 15))
        
        self.info_var = tk.StringVar(value="No video selected")
        ttk.Label(
            info_frame,
            textvariable=self.info_var,
            wraplength=700
        ).grid(sticky="w")
        
        # Progress Section
        progress_frame = ttk.LabelFrame(main_frame, text="Progress", padding="10")
        progress_frame.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(0, 15))
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.progress_var,
            maximum=100,
            mode='determinate',
            length=300
        )
        self.progress_bar.grid(row=0, column=0, sticky="ew", pady=(5, 10))
        progress_frame.grid_columnconfigure(0, weight=1)
        
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(
            progress_frame,
            textvariable=self.status_var
        ).grid(row=1, column=0, sticky="w")
        
        # Start Button
        self.start_button = ttk.Button(
            main_frame,
            text="Start Extraction",
            command=self.start_extraction,
            width=20
        )
        self.start_button.grid(row=6, column=0, columnspan=2, pady=(0, 10))
        
        # Configure grid weights
        main_frame.grid_columnconfigure(1, weight=1)
        video_frame.grid_columnconfigure(1, weight=1)
        output_frame.grid_columnconfigure(1, weight=1)

    def select_video(self):
        """Handle video file selection."""
        file_path = filedialog.askopenfilename(
            title="Select Video File",
            filetypes=[("Video files", "*.mp4 *.avi *.mkv *.mov")]
        )
        
        if file_path:
            try:
                # Test video file
                cap = cv2.VideoCapture(file_path)
                if not cap.isOpened():
                    raise Exception("Unable to open video file")
                
                # Store paths
                self.video_path = file_path
                self.video_path_var.set(file_path)
                
                # Update save directory if checkbox is checked
                if self.same_dir_var.get():
                    video_dir = os.path.dirname(file_path)
                    self.save_directory = video_dir
                    self.save_path_var.set(video_dir)
                
                # Update video information
                self.update_video_info(cap)
                cap.release()
            except Exception as e:
                messagebox.showerror("Error", f"Invalid video file: {str(e)}")
                self.video_path = None
                self.video_path_var.set("")

    def select_save_directory(self):
        """Handle output directory selection."""
        directory = filedialog.askdirectory(title="Select Output Directory")
        if directory:
            try:
                # Convert to 8.3 short path format for paths with non-ASCII characters
                try:
                    import win32api # type: ignore
                    self.save_directory = win32api.GetShortPathName(directory)
                except:
                    self.save_directory = directory
                    
                # Show original path in UI
                self.save_path_var.set(directory)
                
            except Exception as e:
                messagebox.showerror("Error", f"Cannot write to selected directory: {str(e)}")
                self.save_directory = None
                self.save_path_var.set("")
    
    def toggle_output_directory(self):
        """Handle the same directory checkbox toggle."""
        if self.same_dir_var.get():
            if self.video_path:
                video_dir = os.path.dirname(self.video_path)
                self.save_directory = video_dir
                self.save_path_var.set(video_dir)
            self.output_entry.configure(state='disabled')
            self.browse_output_btn.configure(state='disabled')
        else:
            self.output_entry.configure(state='normal')
            self.browse_output_btn.configure(state='normal')
            self.save_path_var.set('')
            self.save_directory = None

    def update_video_info(self, cap=None):
        """Update video information display."""
        try:
            should_release = False
            if cap is None:
                cap = cv2.VideoCapture(self.video_path)
                should_release = True
            
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = int(cap.get(cv2.CAP_PROP_FPS))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            duration = total_frames / fps
            
            self.video_info = {
                'total_frames': total_frames,
                'fps': fps,
                'width': width,
                'height': height,
                'duration': duration
            }
            
            info_text = f"Resolution: {width}x{height} pixels\n"
            info_text += f"Duration: {duration:.2f} seconds ({duration/60:.1f} minutes)\n"
            info_text += f"Total Frames: {total_frames:,}\n"
            info_text += f"Frame Rate: {fps} FPS"
            
            self.info_var.set(info_text)
            
            if should_release:
                cap.release()
        except Exception as e:
            self.info_var.set(f"Error reading video: {str(e)}")

    def validate_inputs(self):
        """Validate all user inputs before starting extraction."""
        if not self.video_path or not os.path.exists(self.video_path):
            messagebox.showerror("Error", "Please select a valid video file.")
            return False
            
        if not self.same_dir_var.get():
            if not self.save_directory or not os.path.exists(self.save_directory):
                messagebox.showerror("Error", "Please select a valid output directory.")
                return False
            
        try:
            frame_count = int(self.frame_count_var.get())
            if frame_count <= 0:
                raise ValueError("Frame count must be positive")
            if frame_count > self.video_info['total_frames']:
                raise ValueError("Frame count cannot exceed total frames in video")
        except ValueError as e:
            messagebox.showerror("Error", str(e))
            return False
            
        return True

    def extract_frames(self):
        """Extract frames from video."""
        cap = None
        try:
            # Open video file
            cap = cv2.VideoCapture(self.video_path)
            if not cap.isOpened():
                raise Exception("Failed to open video file")
    
            # Get frame count information
            total_frames = self.video_info['total_frames']
            desired_frames = int(self.frame_count_var.get())
            frame_interval = max(1, total_frames // desired_frames)
            
            frames_processed = 0
            current_frame = 0
            
            # Create output directory if it doesn't exist
            os.makedirs(self.save_directory, exist_ok=True)
            
            # Get short path name for save directory
            try:
                import win32api # type: ignore
                save_dir = win32api.GetShortPathName(self.save_directory)
            except:
                save_dir = self.save_directory
            
            while frames_processed < desired_frames and self.is_extracting:
                if current_frame >= total_frames:
                    break
    
                cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame)
                ret, frame = cap.read()
                
                if not ret or frame is None:
                    raise Exception(f"Failed to read frame at position {current_frame}")
    
                frame_filename = f"frame_{frames_processed+1:04d}.{self.format_var.get()}"
                save_path = os.path.join(save_dir, frame_filename)
    
                success = cv2.imwrite(save_path, frame)
                if not success:
                    raise Exception(f"Failed to save frame: {frame_filename}")
    
                frames_processed += 1
                current_frame += frame_interval
                
                progress = (frames_processed / desired_frames) * 100
                self.root.after(0, lambda p=progress, f=frames_processed, t=desired_frames: 
                    self.update_progress(p, f"Extracting frame {f}/{t}"))
    
            # Handle completion
            if frames_processed == desired_frames:
                self.root.after(0, lambda: self.complete_extraction(
                    f"Successfully extracted {frames_processed} frames!"
                ))
            else:
                self.root.after(0, lambda: self.complete_extraction(
                    f"Extraction stopped after {frames_processed} frames."
                ))
    
        except Exception as e:
            self.root.after(0, lambda msg=str(e): self.handle_extraction_error(msg))
        
        finally:
            if cap is not None:
                cap.release()
                
    def update_progress(self, progress: float, status: str):
        """Update progress bar and status label."""
        self.progress_var.set(progress)
        self.status_var.set(status)

    def complete_extraction(self, message: str):
        """Handle successful completion of extraction."""
        self.is_extracting = False
        self.start_button.configure(text="Start Extraction", state="normal")
        self.status_var.set("Ready")
        self.progress_var.set(0)
        messagebox.showinfo("Success", message)
        try:
            if self.save_directory:
                os.startfile(self.save_directory)
        except:
            pass

    def handle_extraction_error(self, error_message: str):
        """Handle extraction errors."""
        self.is_extracting = False
        self.start_button.configure(text="Start Extraction", state="normal")
        self.status_var.set("Error occurred")
        self.progress_var.set(0)
        messagebox.showerror("Error", f"An error occurred during extraction:\n{error_message}")

    def start_extraction(self):
        """Start or stop the extraction process."""
        if self.is_extracting:
            self.is_extracting = False
            self.start_button.configure(text="Start Extraction")
            self.status_var.set("Extraction stopped by user")
            return

        if not self.validate_inputs():
            return

        if self.same_dir_var.get():
            self.save_directory = os.path.dirname(self.video_path)

        self.is_extracting = True
        self.start_button.configure(text="Stop Extraction")
        self.progress_var.set(0)
        self.status_var.set("Starting extraction...")

        self.extraction_thread = threading.Thread(target=self.extract_frames)
        self.extraction_thread.daemon = True
        self.extraction_thread.start()

def main():
    root = tk.Tk()
    app = VideoFrameExtractor(root)
    root.mainloop()

if __name__ == "__main__":
    main()
