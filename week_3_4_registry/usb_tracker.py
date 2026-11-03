import winreg
import pandas as pd

def extract_usb_artifacts():
    print("🕵️‍♂️ Querying Windows Registry for historical USB connection tracks...")
    
    # 1. Point directly to the low-level hardware tracking vault inside the system architecture
    registry_path = r"SYSTEM\CurrentControlSet\Enum\USBSTOR"
    
    usb_devices_list = []
    
    try:
        # 2. Open the main local machine registry hive link
        # HKEY_LOCAL_MACHINE contains settings that apply to the entire machine, not just one user
        main_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, registry_path)
    except FileNotFoundError:
        print("❌ Could not access or find the USBSTOR registry location.")
        return

    # 3. Read the registry sub-folders using an extraction loop
    # winreg uses a counter index number to step through directories one-by-one
    index = 0
    while True:
        try:
            # Enumerate gets the name of the sub-folder (e.g., "Disk&Ven_SanDisk&Prod_Cruzer...")
            device_folder_name = winreg.EnumKey(main_key, index)
            
            # Open that sub-folder to get to the nested unique serial numbers
            device_key_path = f"{registry_path}\\{device_folder_name}"
            device_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, device_key_path)
            
            # Every hardware device has a nested folder containing its unique hardware serial number
            serial_index = 0
            while True:
                try:
                    serial_number = winreg.EnumKey(device_key, serial_index)
                    
                    # Parse the device string to extract clean Vendor and Product models
                    # The raw string looks like: Disk&Ven_SanDisk&Prod_Cruzer_Glide&Rev_1.00
                    vendor_name = "Unknown Vendor"
                    product_name = "Unknown Product"
                    
                    if "Ven_" in device_folder_name:
                        parts = device_folder_name.split("&")
                        for part in parts:
                            if part.startswith("Ven_"):
                                vendor_name = part.replace("Ven_", "")
                            if part.startswith("Prod_"):
                                product_name = part.replace("Prod_", "")
                    
                    # Stash all parsed information into a structured data bundle dictionary row
                    usb_devices_list.append({
                        "Device_Hardware_ID": device_folder_name,
                        "Vendor": vendor_name,
                        "Product": product_name,
                        "Serial_Number": serial_number
                    })
                    
                    serial_index += 1
                except OSError:
                    # No more unique serial sub-keys left inside this device folder
                    break
            
            winreg.CloseKey(device_key)
            index += 1
            
        except OSError:
            # Out of bounds exception: We have successfully scanned through all devices in the registry
            break
            
    winreg.CloseKey(main_key)
    
    if not usb_devices_list:
        print("⚠️ No structural USB connection records discovered in this machine's Registry hive.")
        return

    # 4. Map the memory records directly into a structured Pandas DataFrame grid table
    df = pd.DataFrame(usb_devices_list)
    
    # Export results to an analyst-ready spreadsheet report
    output_file = "Forensic_USB_Registry_Logs.xlsx"
    df.to_excel(output_file, index=False)
    print(f"🎉 Success! Extracted USB hardware logs saved to: {output_file}")

if __name__ == "__main__":
    extract_usb_artifacts()
 