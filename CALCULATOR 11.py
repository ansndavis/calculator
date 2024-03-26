import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import simpledialog
from tkinter import messagebox

# Global variable to store the file path
selected_file_path = None

def get_nominal(min_val, max_val):
    return (min_val + max_val) / 2

def update_nominal(min_entry, max_entry, result_label):
    try:
        min_val = min_entry.get().strip()
        max_val = max_entry.get().strip()
        if min_val and not max_val:
            max_val = min_val
        elif max_val and not min_val:
            min_val = max_val

        min_val = float(min_val)
        max_val = float(max_val)

        if unit_var.get() == "inches":
            min_val *= 25.4
            max_val *= 25.4

        nominal = get_nominal(min_val, max_val)
        result_label.config(text=f"{nominal:.3f}", foreground="red")
        return nominal
    except ValueError:
        result_label.config(text="0.000", foreground="red")
        return None

def calculate_all():
    summary_text = "Summary:\n"
    nominal_values = {}

    for label, (min_entry, max_entry), result_label in zip(labels, entries, result_labels):
        nominal = update_nominal(min_entry, max_entry, result_label)
        if nominal is not None:
            nominal_values[label.replace(" (optional)", "").replace(" (auto)", "")] = nominal
            summary_text += f"{label}: {nominal:.3f} {unit_var.get()}\n"

    part_type = part_type_combobox.get()
    package_mount = package_mount_combobox.get()
    summary_text += f"Part Type: {part_type}\nPackage Mount: {package_mount}\n"

    if bga_var.get():
        bga_thickness = nominal_values.get("Package Thickness", 0)
        if bga_thickness > 0:
            overmold_thickness = bga_thickness * 0.67
            laminate_thickness = bga_thickness * 0.33
            summary_text += f"BGA Overmold Thickness: {overmold_thickness:.3f} mm\n"
            summary_text += f"BGA Laminate Thickness: {laminate_thickness:.3f} mm\n"

    if "Package Thickness" in nominal_values and "Lead Standoff" in nominal_values and include_standoff_var.get():
        package_thickness = nominal_values["Package Thickness"] - nominal_values["Lead Standoff"]
        lead_thickness = nominal_values.get("Lead Thickness", 0) / 2
        if "Lead Height" not in nominal_values:
            lead_height = (nominal_values["Package Thickness"] * (0.5 if lead_height_ratio_var.get() == "1/2" else 2/3)) + nominal_values["Lead Standoff"] - lead_thickness
        else:
            lead_height = nominal_values["Lead Height"] - lead_thickness
        summary_text += f"Thickness Minus Standoff: {package_thickness:.3f} mm\n"
        summary_text += f"Adjusted Lead Height: {lead_height:.3f} mm\n"

    if die_var.get() and "Package Width" in nominal_values:
        package_width = nominal_values["Package Width"]
        package_length = nominal_values.get("Package Length", package_width)  # Incorporate package length
        if part_type_mode_var.get() == "Diode":
            die_width = die_length = package_width / 2
        elif part_type_mode_var.get() == "Flag":
            try:
                flag_length = float(flag_length_entry.get())
                flag_width = float(flag_width_entry.get())
                die_width = flag_width - 0.1
                die_length = flag_length - 0.1
            except ValueError:
                die_width = die_length = 0  # Reset to 0 if the flag entries are invalid
        elif part_type_mode_var.get() == "Standard":  # If mode is "Standard"
            die_width = package_width / 2  # Divide package width by 2
            die_length = package_length / 2  # Divide package length by 2
        else:  # Default to "Standard" if no specific mode is selected or applicable
            die_width = die_length = package_width / 2  # Fallback if no length is specified
        summary_text += f"Die Width: {die_width:.3f} mm\n"
        summary_text += f"Die Length: {die_length:.3f} mm\n"

    if "Overall Width" in nominal_values and "Package Width" in nominal_values and "Lead Foot Length" in nominal_values:
        overall_width = nominal_values["Overall Width"]
        package_width = nominal_values["Package Width"]
        lead_foot_length = nominal_values["Lead Foot Length"]
        lead_shoulder = ((overall_width - package_width) / 2) - lead_foot_length
        summary_text += f"Lead Shoulder Width: {lead_shoulder:.3f} mm\n"

    summary_label.config(text=summary_text, foreground="red")

def clear_all():
    for min_entry, max_entry in entries:
        min_entry.delete(0, tk.END)
        max_entry.delete(0, tk.END)
    part_type_combobox.set('')
    package_mount_combobox.set('')
    summary_label.config(text="Summary:", foreground="red")

def export_summary():
    global selected_file_path  # Use the global variable
    if selected_file_path is None:  # If file path is not selected yet, prompt to select
        selected_file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")], title="Save Summary As")
        if not selected_file_path:  # If user canceled, return
            return
    ref_des = simpledialog.askstring("Export Summary", "Enter Reference Designator:")
    if ref_des is None:
        return  # User canceled the dialog
    try:
        with open(selected_file_path, "a") as file:
            file.write(f"{ref_des}\n")
            file.write(summary_label.cget("text") + "\n")
        messagebox.showinfo("Exported", "Summary exported successfully.")
    except FileNotFoundError:
        messagebox.showerror("Error", "The selected file is no longer available. Please select a new file.")
        selected_file_path = None  # Reset the selected file path to allow the user to select a new one
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred while exporting the summary: {str(e)}")

root = tk.Tk()
root.title("Nominal Value Calculator")
root.geometry('800x600')

main_frame = ttk.Frame(root)
main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

left_frame = ttk.Frame(main_frame)
left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

right_frame = ttk.Frame(main_frame)
right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)

scrollbar = ttk.Scrollbar(left_frame, orient="vertical")
canvas = tk.Canvas(left_frame, yscrollcommand=scrollbar.set, borderwidth=0)
scrollbar.config(command=canvas.yview)
scrollbar.pack(side="right", fill="y")
canvas.pack(side="left", fill="both", expand=True)

scrollable_frame = ttk.Frame(canvas)
canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

labels = [
    "Overall Width", "Package Length", "Package Width", "Package Thickness",
    "Pad Length", "Pad Width", "Pad Pitch",
    "Lead Height", "Lead Width", "Lead Thickness", "Lead Foot Length",
    "Lead Pitch", "Lead Shoulder", "Lead Standoff",
    "Sink Length", "Sink Width", "Sink Thickness",
    "Die Length", "Die Width", "Die Thickness",
    "Flag Length", "Flag Width", "Flag Thickness"
]

entries = []
result_labels = []

part_types = [
    "AVX", "AXIAL", "BGA", "BOX", "BTC", "CBEND", "CBGA", "CDIP", "CC", "CGA",
    "CQFP", "DFN", "DIE", "DIP", "DISC", "DPAK", "HSOP", "KEMET", "LCCC", "LSOP",
    "MELF", "MSOP", "OTHER", "PDIP", "PDSO", "PLCC", "PQFP", "QFJ", "QFN", "QFP",
    "RADIAL", "SIP", "SM", "SOD", "SOIC", "SOJ", "SON", "SOT", "SPAK", "SSOP",
    "TO", "TSOP", "TSSOP", "USON", "VCHIP"
]
package_mounts = ["SMT", "TH"]

unit_var = tk.StringVar(value="mm")
include_standoff_var = tk.BooleanVar(value=True)
lead_height_ratio_var = tk.StringVar(value="1/2")
die_var = tk.BooleanVar(value=False)
bga_var = tk.BooleanVar(value=False)
part_type_mode_var = tk.StringVar(value="Standard")

options_frame = ttk.Frame(right_frame)
options_frame.pack(fill=tk.X, pady=10)

part_type_combobox = ttk.Combobox(options_frame, values=part_types, width=15)
part_type_combobox.pack(side=tk.TOP, fill=tk.X, padx=5, pady=2)
package_mount_combobox = ttk.Combobox(options_frame, values=package_mounts, width=15)
package_mount_combobox.pack(side=tk.TOP, fill=tk.X, padx=5, pady=2)

ttk.Radiobutton(options_frame, text="mm", variable=unit_var, value="mm", command=calculate_all).pack(side=tk.TOP, fill=tk.X, padx=5, pady=2)
ttk.Radiobutton(options_frame, text="inches", variable=unit_var, value="inches", command=calculate_all).pack(side=tk.TOP, fill=tk.X, padx=5, pady=2)
ttk.Checkbutton(options_frame, text="Include Standoff in Thickness", variable=include_standoff_var, command=calculate_all).pack(side=tk.TOP, fill=tk.X, padx=5, pady=2)

ttk.Checkbutton(options_frame, text="Include Die Calculation", variable=die_var, command=calculate_all).pack(side=tk.TOP, fill=tk.X, padx=5, pady=2)

# Lead Height Ratio Radio Buttons
ttk.Radiobutton(options_frame, text="1/2", variable=lead_height_ratio_var, value="1/2", command=calculate_all).pack(side=tk.TOP, fill=tk.X, padx=5, pady=2)
ttk.Radiobutton(options_frame, text="2/3", variable=lead_height_ratio_var, value="2/3", command=calculate_all).pack(side=tk.TOP, fill=tk.X, padx=5, pady=2)

# Part Type Mode Radio Buttons
ttk.Radiobutton(options_frame, text="Standard", variable=part_type_mode_var, value="Standard", command=calculate_all).pack(side=tk.TOP, fill=tk.X, padx=5, pady=2)
ttk.Radiobutton(options_frame, text="Diode", variable=part_type_mode_var, value="Diode", command=calculate_all).pack(side=tk.TOP, fill=tk.X, padx=5, pady=2)
ttk.Radiobutton(options_frame, text="Flag", variable=part_type_mode_var, value="Flag", command=calculate_all).pack(side=tk.TOP, fill=tk.X, padx=5, pady=2)

ttk.Checkbutton(options_frame, text="BGA Mode", variable=bga_var, command=calculate_all).pack(side=tk.TOP, fill=tk.X, padx=5, pady=2)

# Flag Length and Flag Width Entries
flag_length_label = ttk.Label(scrollable_frame, text="Flag Length (mm):", width=20)
flag_length_label.pack(padx=5, pady=2)
flag_length_entry = ttk.Entry(scrollable_frame, width=10)
flag_length_entry.pack(padx=5, pady=2)

flag_width_label = ttk.Label(scrollable_frame, text="Flag Width (mm):", width=20)
flag_width_label.pack(padx=5, pady=2)
flag_width_entry = ttk.Entry(scrollable_frame, width=10)
flag_width_entry.pack(padx=5, pady=2)

for label in labels:
    row = ttk.Frame(scrollable_frame)
    row.pack(fill=tk.X, padx=5, pady=2)
    lbl = ttk.Label(row, text=label, width=20)
    lbl.pack(side=tk.LEFT)
    min_entry = ttk.Entry(row, width=10)
    min_entry.pack(side=tk.LEFT, padx=5)
    max_entry = ttk.Entry(row, width=10)
    max_entry.pack(side=tk.LEFT, padx=5)
    result_nominal_label = ttk.Label(row, text="0.000", width=10, foreground="red")
    result_nominal_label.pack(side=tk.LEFT, padx=5)
    entries.append((min_entry, max_entry))
    result_labels.append(result_nominal_label)

scrollable_frame.update_idletasks()
canvas.config(scrollregion=canvas.bbox("all"))

summary_label = ttk.Label(right_frame, text="Summary:", anchor="nw", justify=tk.LEFT, foreground="red")
summary_label.pack(pady=10, padx=5, fill=tk.BOTH, expand=True)

ttk.Button(right_frame, text="Clear All", command=clear_all).pack(side=tk.BOTTOM, padx=5, pady=5)
ttk.Button(right_frame, text="Export Summary", command=export_summary).pack(side=tk.BOTTOM, padx=5, pady=5)

for min_entry, max_entry in entries:
    min_entry.bind('<KeyRelease>', lambda event: calculate_all())
    max_entry.bind('<KeyRelease>', lambda event: calculate_all())
part_type_combobox.bind('<<ComboboxSelected>>', lambda event: calculate_all())
package_mount_combobox.bind('<<ComboboxSelected>>', lambda event: calculate_all())

root.mainloop()
