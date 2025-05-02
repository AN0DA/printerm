import logging
import tkinter as tk
from tkinter import font as tkfont
from tkinter import messagebox, scrolledtext, ttk

from printerm.core.config import (
    PRINT_TEMPLATE_FOLDER,
    get_chars_per_line,
    get_check_for_updates,
    get_enable_special_letters,
    get_printer_ip,
    set_chars_per_line,
    set_check_for_updates,
    set_enable_special_letters,
    set_printer_ip,
)
from printerm.core.utils import TemplateRenderer, compute_agenda_variables
from printerm.printing.printer import ThermalPrinter
from printerm.templates.template_manager import TemplateManager

logger = logging.getLogger(__name__)


class MainWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Thermal Printer Application")
        self.root.geometry("700x500")
        self.template_manager = TemplateManager(PRINT_TEMPLATE_FOLDER)
        self.template_renderer = TemplateRenderer(self.template_manager)
        self.init_ui()

    def init_ui(self):
        # Create frame for better layout
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Add title
        title_label = ttk.Label(
            main_frame, 
            text="Thermal Printer Application", 
            font=("TkDefaultFont", 16, "bold")
        )
        title_label.pack(pady=(0, 20))
        
        # Add instructions
        instruction_label = ttk.Label(
            main_frame,
            text="Select a template to print:",
            font=("TkDefaultFont", 12)
        )
        instruction_label.pack(pady=(0, 10))

        # Create main content area with two panels
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10)

        # Left panel for template buttons
        button_frame = ttk.LabelFrame(content_frame, text="Templates")
        button_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        # Right panel for template preview with fixed width
        preview_frame = ttk.LabelFrame(content_frame, text="Template Preview")
        
        # Calculate fixed width for preview based on character count
        # For monospace font, measure the width of a single character
        temp_label = tk.Label(self.root, font=("Courier", 10))
        temp_label.config(text="M")  # Use a wide character for measurement
        temp_label.pack()
        char_width = temp_label.winfo_reqwidth()
        temp_label.destroy()
        
        # Get character width from config
        chars_per_line = get_chars_per_line()
        
        # Set fixed width in pixels (chars + some padding for scrollbar and borders)
        frame_width = (chars_per_line + 5) * char_width
        preview_frame.config(width=frame_width)
        
        # Prevent preview from expanding horizontally
        preview_frame.pack(side=tk.RIGHT, fill=tk.Y, expand=False, padx=(5, 0))
        
        # Ensure preview frame maintains fixed width
        preview_frame.pack_propagate(False)
        
        # Set up monospaced preview text widget
        self.preview_text = scrolledtext.ScrolledText(
            preview_frame, 
            wrap=tk.WORD, 
            width=chars_per_line + 5,  # Set exact width in characters
            height=15, 
            font=("Courier", 10)
        )
        self.preview_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.preview_text.config(state=tk.DISABLED)
        
        # Add width indicator at the bottom of preview
        width_frame = ttk.Frame(preview_frame)
        width_frame.pack(fill=tk.X, pady=(0, 5))
        
        width_label = ttk.Label(
            width_frame, 
            text=f"Printer width: {chars_per_line} characters", 
            font=("TkDefaultFont", 8)
        )
        width_label.pack(side=tk.LEFT, padx=5)

        # Create a scrollable canvas for buttons if there are many templates
        templates = self.template_manager.list_templates()
        
        for template_name in templates:
            # Make button names more user-friendly
            display_name = template_name.replace("_", " ").title()
            
            # Create a frame for each template with preview and print buttons
            template_frame = ttk.Frame(button_frame)
            template_frame.pack(fill=tk.X, padx=5, pady=5)
            
            template_button = ttk.Button(
                template_frame,
                text=display_name,
                command=lambda t=template_name: self.show_template_preview(t),
                width=15
            )
            template_button.pack(side=tk.LEFT, padx=(5, 2))
            
            print_button = ttk.Button(
                template_frame,
                text="Print",
                command=lambda t=template_name: self.open_template_dialog(t),
                width=8
            )
            print_button.pack(side=tk.RIGHT, padx=(2, 5))

        # Add settings button at the bottom
        settings_frame = ttk.Frame(main_frame)
        settings_frame.pack(fill=tk.X, pady=10)
        
        settings_button = ttk.Button(
            settings_frame,
            text="Settings",
            command=self.open_settings_dialog,
            width=15
        )
        settings_button.pack(side=tk.RIGHT, padx=10)
        
        # Show the first template preview by default if templates exist
        if templates:
            self.show_template_preview(templates[0])

    def show_template_preview(self, template_name):
        """Show a preview of the selected template in the preview panel"""
        try:
            template = self.template_manager.get_template(template_name)

            # Enable text widget for editing
            self.preview_text.config(state=tk.NORMAL)
            self.preview_text.delete(1.0, tk.END)

            # Create a visually appealing preview
            self.preview_text.insert(
                tk.END, f"TEMPLATE: {template.get('name', template_name.replace('_', ' ').title())}\n", "title"
            )
            self.preview_text.insert(tk.END, f"{'-' * 40}\n", "separator")

            if "description" in template:
                self.preview_text.insert(tk.END, f"{template['description']}\n\n", "description")

            self.preview_text.insert(tk.END, "REQUIRED INPUTS:\n", "subtitle")
            if template.get("variables", []):
                for var in template.get("variables", []):
                    self.preview_text.insert(tk.END, f"• {var['description']}")
                    if var.get("required", False):
                        self.preview_text.insert(tk.END, " (required)")
                    self.preview_text.insert(tk.END, "\n")
            else:
                self.preview_text.insert(tk.END, "None\n")

            self.preview_text.insert(tk.END, f"\n{'-' * 40}\n", "separator")
            self.preview_text.insert(tk.END, "SAMPLE OUTPUT:\n", "subtitle")

            # Set visual width indicator to match printer width
            chars_per_line = get_chars_per_line()
            self.preview_text.insert(tk.END, f"<{'-' * (chars_per_line - 2)}>\n", "width_indicator")

            # Generate a sample preview using placeholder values
            sample_context = {}
            if template_name == "agenda":
                sample_context = compute_agenda_variables()
            else:
                for var in template.get("variables", []):
                    placeholder = f"[{var['description']}]"
                    sample_context[var["name"]] = placeholder

            try:
                segments = self.template_renderer.render_from_template(template_name, sample_context)
                preview_text = self.format_segments_for_preview(segments, chars_per_line)
                self.preview_text.insert(tk.END, preview_text)
            except Exception as e:
                self.preview_text.insert(tk.END, f"Error generating preview: {e}")

            # Configure text tags for styling
            self.preview_text.tag_configure("title", font=("TkDefaultFont", 12, "bold"))
            self.preview_text.tag_configure("subtitle", font=("TkDefaultFont", 10, "bold"))
            self.preview_text.tag_configure("description", font=("TkDefaultFont", 10, "italic"))
            self.preview_text.tag_configure("separator", foreground="gray")
            self.preview_text.tag_configure("width_indicator", foreground="red")

            # Disable text widget to prevent editing
            self.preview_text.config(state=tk.DISABLED)

        except Exception as e:
            logger.error(f"Error showing template preview for '{template_name}': {e}", exc_info=True)
            self.preview_text.config(state=tk.NORMAL)
            self.preview_text.delete(1.0, tk.END)
            self.preview_text.insert(tk.END, f"Error loading template: {e}")
            self.preview_text.config(state=tk.DISABLED)

    def format_segments_for_preview(self, segments, chars_per_line=32):
        """Format rendered segments into a plain text preview with width limits"""
        result = ""
        for segment in segments:
            text = segment["text"]
            styles = segment.get("styles", {})

            # Word wrap text to match printer width
            wrapped_text = ""
            for line in text.split('\n'):
                # Keep track of current line length
                current_line = ""
                for word in line.split(' '):
                    # If adding this word would exceed chars_per_line
                    if len(current_line) + len(word) + 1 > chars_per_line:
                        # Add current line to wrapped text and start a new line
                        wrapped_text += current_line.rstrip() + "\n"
                        current_line = word + " "
                    else:
                        # Add word to current line
                        current_line += word + " "

                # Add the last line
                if current_line:
                    wrapped_text += current_line.rstrip() + "\n"

            # Add styling indicators
            text = wrapped_text
            if styles.get("bold", False):
                text = f"*{text}*"
            if styles.get("italic", False):
                text = f"_{text}_"
            if styles.get("double_width", False) or styles.get("double_height", False):
                text = f"[LARGE] {text}"

            # Add text with appropriate alignment indicator
            align = styles.get("align", "left")
            if align == "center":
                result += f"[CENTER] {text}"
            elif align == "right":
                result += f"[RIGHT] {text}"
            else:
                result += text

        return result

    def open_template_dialog(self, template_name):
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Print {template_name.replace('_', ' ').title()}")
        dialog.geometry("600x500")
        dialog.transient(self.root)
        dialog.grab_set()

        TemplateDialog(dialog, template_name, self.template_manager, self.template_renderer)

    def open_settings_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Settings")
        dialog.geometry("500x300")
        dialog.transient(self.root)
        dialog.grab_set()

        SettingsDialog(dialog)


class TemplateDialog:
    def __init__(self, parent, template_name, template_manager, template_renderer):
        self.parent = parent
        self.template_name = template_name
        self.template_manager = template_manager
        self.template_renderer = template_renderer
        self.chars_per_line = get_chars_per_line()
        self.inputs = {}
        self.preview = None
        self.init_ui()

    def init_ui(self):
        template = self.template_manager.get_template(self.template_name)
        
        # Main frame
        main_frame = ttk.Frame(self.parent, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Add a PanedWindow for form and preview
        paned = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, pady=(10, 20))
        
        # Form frame on the left
        form_container = ttk.Frame(paned)
        paned.add(form_container, weight=1)
        
        # Preview frame on the right - with fixed width
        preview_container = ttk.LabelFrame(paned, text="Print Preview")
        
        # Calculate pixel width based on character count
        # For monospace font, measure the width of a single character
        temp_label = tk.Label(self.parent, font=("Courier", 10))
        temp_label.config(text="M")  # Use a wide character for measurement
        temp_label.pack()
        char_width = temp_label.winfo_reqwidth()
        temp_label.destroy()
        
        # Set fixed width in pixels (chars + some padding)
        frame_width = (self.chars_per_line + 5) * char_width
        preview_container.config(width=frame_width)
        
        # Prevent preview_container from expanding horizontally
        paned.add(preview_container, weight=0)
        
        # Set up the preview area with monospaced font for accurate character width
        monospace_font = tkfont.Font(family="Courier", size=10)
        self.preview = scrolledtext.ScrolledText(
            preview_container, 
            wrap=tk.WORD, 
            width=self.chars_per_line,  # Set width exactly to chars_per_line
            height=15,
            font=monospace_font
        )
        self.preview.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.preview.config(state=tk.DISABLED)
        
        # Add print width indicator
        width_frame = ttk.Frame(preview_container)
        width_frame.pack(fill=tk.X, pady=(0, 5))
        
        width_label = ttk.Label(
            width_frame, 
            text=f"Printer width: {self.chars_per_line} characters", 
            font=("TkDefaultFont", 8)
        )
        width_label.pack(side=tk.LEFT, padx=5)
        
        # Make sure the preview container maintains its fixed width
        preview_container.pack_propagate(False)
        
        # Title in form container
        title_label = ttk.Label(
            form_container,
            text=f"Print {template.get('name', self.template_name.replace('_', ' ').title())}",
            font=("TkDefaultFont", 14, "bold"),
        )
        title_label.pack(pady=(0, 10))

        # Description if available
        if "description" in template:
            desc_label = ttk.Label(form_container, text=template.get("description", ""), wraplength=250)
            desc_label.pack(pady=(0, 15))

        # Form for variables
        form_frame = ttk.Frame(form_container)
        form_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        row = 0
        for var in template.get("variables", []):
            label = ttk.Label(form_frame, text=var["description"] + ":")
            label.grid(row=row, column=0, sticky="w", padx=5, pady=5)

            if var.get("markdown", False):
                input_field = scrolledtext.ScrolledText(form_frame, height=5, width=30)
                input_field.grid(row=row, column=1, sticky="ew", padx=5, pady=5)
            else:
                input_field = ttk.Entry(form_frame, width=30)
                input_field.grid(row=row, column=1, sticky="ew", padx=5, pady=5)
                input_field.bind("<KeyRelease>", lambda e, template_name=self.template_name: self.update_preview())

            self.inputs[var["name"]] = input_field
            row += 1

        # Add some stretch space if few fields
        if row < 3:
            form_frame.grid_rowconfigure(row, weight=1)

        form_frame.grid_columnconfigure(1, weight=1)

        # Preview button
        preview_button = ttk.Button(form_container, text="Update Preview", command=self.update_preview, width=15)
        preview_button.pack(pady=(5, 10))

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)

        cancel_button = ttk.Button(button_frame, text="Cancel", command=self.parent.destroy, width=10)
        cancel_button.pack(side=tk.RIGHT, padx=5)

        print_button = ttk.Button(button_frame, text="Print", command=self.print_template, width=10)
        print_button.pack(side=tk.RIGHT, padx=5)

        # Initialize preview
        self.update_preview()

    def update_preview(self):
        """Update the print preview based on current input values"""
        template = self.template_manager.get_template(self.template_name)
        context = {}

        try:
            # Get current values from form
            if self.template_name == "agenda":
                context = compute_agenda_variables()
            else:
                for var in template.get("variables", []):
                    input_field = self.inputs[var["name"]]
                    if isinstance(input_field, scrolledtext.ScrolledText):
                        value = input_field.get("1.0", tk.END).strip()
                    else:
                        value = input_field.get()

                    # If field is empty, use placeholder
                    if not value:
                        value = f"[{var['description']}]"

                    context[var["name"]] = value

            # Generate preview
            segments = self.template_renderer.render_from_template(self.template_name, context)

            # Update preview text
            self.preview.config(state=tk.NORMAL)
            self.preview.delete(1.0, tk.END)

            # Add width indicator
            self.preview.insert(tk.END, f"<{'-' * (self.chars_per_line - 2)}>\n", "width_indicator")

            # Convert segments to formatted text for preview
            for segment in segments:
                text = segment["text"]
                styles = segment.get("styles", {})

                # Word wrap text to match printer width
                wrapped_text = ""
                for line in text.split('\n'):
                    # Keep track of current line length
                    current_line = ""
                    for word in line.split(' '):
                        # If adding this word would exceed chars_per_line
                        if len(current_line) + len(word) + 1 > self.chars_per_line:
                            # Add current line to wrapped text with tag
                            tag_name = f"tag_{id(line)}_{len(wrapped_text)}"
                            self.preview.insert(tk.END, current_line.rstrip() + "\n", tag_name)
                            current_line = word + " "
                        else:
                            # Add word to current line
                            current_line += word + " "

                    # Add the last line with tag
                    if current_line:
                        tag_name = f"tag_{id(line)}_{len(wrapped_text)}"
                        self.preview.insert(tk.END, current_line.rstrip() + "\n", tag_name)

                        # Configure tag with appropriate styles
                        font_attrs = ("Courier", 10)
                        if styles.get("bold", False):
                            font_attrs = font_attrs + ("bold",)
                        if styles.get("italic", False):
                            font_attrs = font_attrs + ("italic",)

                        self.preview.tag_configure(tag_name, font=font_attrs)

                        # Handle alignment (approximate in the preview)
                        align = styles.get("align", "left")
                        if align == "center":
                            self.preview.tag_configure(tag_name, justify=tk.CENTER)
                        elif align == "right":
                            self.preview.tag_configure(tag_name, justify=tk.RIGHT)

            # Configure width indicator style
            self.preview.tag_configure("width_indicator", foreground="red")

            self.preview.config(state=tk.DISABLED)

        except Exception as e:
            logger.error(f"Error updating preview: {e}", exc_info=True)
            self.preview.config(state=tk.NORMAL)
            self.preview.delete(1.0, tk.END)
            self.preview.insert(tk.END, f"Error generating preview: {e}")
            self.preview.config(state=tk.DISABLED)

    def print_template(self):
        template = self.template_manager.get_template(self.template_name)
        context = {}

        if self.template_name == "agenda":
            context = compute_agenda_variables()
        else:
            for var in template.get("variables", []):
                input_field = self.inputs[var["name"]]
                if isinstance(input_field, scrolledtext.ScrolledText):
                    context[var["name"]] = input_field.get("1.0", tk.END).strip()
                else:
                    context[var["name"]] = input_field.get()

                # Basic validation for required fields
                if var.get("required", False) and not context[var["name"]]:
                    messagebox.showerror("Error", f"Please enter {var['description']}")
                    return

        try:
            ip_address = get_printer_ip()
            with ThermalPrinter(ip_address, self.template_manager) as printer:
                printer.print_template(self.template_name, context)
            messagebox.showinfo("Success", f"Printed using template '{self.template_name}'.")
            self.parent.destroy()
        except Exception as e:
            logger.error(f"Error printing template '{self.template_name}': {e}", exc_info=True)
            messagebox.showerror("Error", f"Failed to print: {e}")


class SettingsDialog:
    def __init__(self, parent):
        self.parent = parent
        self.init_ui()

    def init_ui(self):
        # Main frame with padding
        main_frame = ttk.Frame(self.parent, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title_label = ttk.Label(main_frame, text="Printer Settings", font=("TkDefaultFont", 14, "bold"))
        title_label.pack(pady=(0, 15))

        # Settings form
        form_frame = ttk.Frame(main_frame)
        form_frame.pack(fill=tk.BOTH, expand=True)

        # IP Address
        ip_label = ttk.Label(form_frame, text="Printer IP Address:")
        ip_label.grid(row=0, column=0, sticky="w", padx=5, pady=8)

        self.ip_var = tk.StringVar()
        try:
            self.ip_var.set(get_printer_ip())
        except ValueError:
            self.ip_var.set("")

        ip_entry = ttk.Entry(form_frame, textvariable=self.ip_var, width=30)
        ip_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=8)

        # Characters per line
        chars_label = ttk.Label(form_frame, text="Characters Per Line:")
        chars_label.grid(row=1, column=0, sticky="w", padx=5, pady=8)

        self.chars_var = tk.StringVar()
        self.chars_var.set(str(get_chars_per_line()))
        chars_entry = ttk.Entry(form_frame, textvariable=self.chars_var, width=30)
        chars_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=8)

        # Enable Special Letters
        special_label = ttk.Label(form_frame, text="Enable Special Letters:")
        special_label.grid(row=2, column=0, sticky="w", padx=5, pady=8)

        self.special_var = tk.BooleanVar()
        self.special_var.set(get_enable_special_letters())
        special_check = ttk.Checkbutton(form_frame, variable=self.special_var)
        special_check.grid(row=2, column=1, sticky="w", padx=5, pady=8)

        # Check for Updates
        updates_label = ttk.Label(form_frame, text="Check for Updates:")
        updates_label.grid(row=3, column=0, sticky="w", padx=5, pady=8)

        self.updates_var = tk.BooleanVar()
        self.updates_var.set(get_check_for_updates())
        updates_check = ttk.Checkbutton(form_frame, variable=self.updates_var)
        updates_check.grid(row=3, column=1, sticky="w", padx=5, pady=8)

        # Add some space
        form_frame.grid_rowconfigure(4, weight=1)

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)

        cancel_button = ttk.Button(button_frame, text="Cancel", command=self.parent.destroy, width=10)
        cancel_button.pack(side=tk.RIGHT, padx=5)

        save_button = ttk.Button(button_frame, text="Save", command=self.save_settings, width=10)
        save_button.pack(side=tk.RIGHT, padx=5)

    def save_settings(self):
        # Save IP address
        ip_address = self.ip_var.get()
        if not ip_address:
            messagebox.showerror("Error", "Please enter a printer IP address")
            return
        set_printer_ip(ip_address)

        # Save chars per line
        try:
            chars_per_line = int(self.chars_var.get())
            if chars_per_line <= 0:
                raise ValueError("Characters per line must be a positive number")
            set_chars_per_line(chars_per_line)
            # Notify that width setting changed and previews will reflect it on restart
            messagebox.showinfo(
                "Width Setting Changed",
                "The characters per line setting has been updated. "
                "Template previews will use this new width the next time you restart the application."
            )
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid number for characters per line: {e}")
            return

        # Save special letters setting
        set_enable_special_letters(self.special_var.get())

        # Save check for updates setting
        set_check_for_updates(self.updates_var.get())

        messagebox.showinfo("Success", "Settings saved successfully")
        self.parent.destroy()


def main():
    root = tk.Tk()
    MainWindow(root)
    # Apply a theme if available
    try:
        style = ttk.Style()
        style.theme_use("clam")  # Use a more modern theme if available
    except ttk.TclError:
        pass  # Use default theme if clam is not available
    root.mainloop()


if __name__ == "__main__":
    main()
