import os
import glob
from pathlib import Path

def merge_md_files(input_directory, output_file="merged_output.md"):
    """
    Merge all .md files in a directory into a single file with headers and index.
    
    Args:
        input_directory: Path to directory containing .md files
        output_file: Name of the output merged file
    """
    
    # Get all .md files in the directory
    md_files = glob.glob(os.path.join(input_directory, "*.md"))
    
    # Sort files alphabetically (you can modify sorting logic if needed)
    md_files.sort()
    
    if not md_files:
        print(f"No .md files found in {input_directory}")
        return
    
    print(f"Found {len(md_files)} .md files")
    
    # Create the output file
    with open(output_file, 'w', encoding='utf-8') as outfile:
        
        # Write main title
        outfile.write("# MASTER INDEX\n\n")
        outfile.write(f"**Total Files Merged:** {len(md_files)}\n\n")
        outfile.write("---\n\n")
        
        # Write table of contents / index
        outfile.write("## 📑 TABLE OF CONTENTS\n\n")
        
        for idx, filepath in enumerate(md_files, 1):
            filename = os.path.basename(filepath)
            # Remove .md extension for display
            display_name = filename.replace('.md', '')
            outfile.write(f"{idx}. [{display_name}](#{display_name.lower().replace(' ', '-')})\n")
        
        outfile.write("\n---\n\n")
        
        # Now write the content of each file
        for idx, filepath in enumerate(md_files, 1):
            filename = os.path.basename(filepath)
            display_name = filename.replace('.md', '')
            
            # Write file header with index
            outfile.write(f"## {idx}. {display_name}\n\n")
            outfile.write(f"*Source: {filename}*\n\n")
            
            # Read and write the content of the file
            try:
                with open(filepath, 'r', encoding='utf-8') as infile:
                    content = infile.read()
                    outfile.write(content)
                    outfile.write("\n\n")  # Add spacing between files
            except Exception as e:
                outfile.write(f"*Error reading file: {e}*\n\n")
            
            # Add a separator between files (except after the last one)
            if idx < len(md_files):
                outfile.write("---\n\n")
    
    print(f"Successfully merged {len(md_files)} files into {output_file}")

def merge_with_custom_order(input_directory, output_file="merged_output.md", custom_order=None):
    """
    Merge files with custom ordering.
    
    Args:
        input_directory: Path to directory containing .md files
        output_file: Name of the output merged file
        custom_order: List of filenames in desired order (if None, alphabetical order is used)
    """
    
    if custom_order:
        # Use custom order if provided
        md_files = []
        for filename in custom_order:
            filepath = os.path.join(input_directory, filename)
            if os.path.exists(filepath):
                md_files.append(filepath)
            else:
                print(f"Warning: {filename} not found in {input_directory}")
        
        # Add any remaining files not in custom order
        all_files = glob.glob(os.path.join(input_directory, "*.md"))
        for filepath in all_files:
            if filepath not in md_files:
                md_files.append(filepath)
    else:
        md_files = glob.glob(os.path.join(input_directory, "*.md"))
        md_files.sort()
    
    if not md_files:
        print(f"No .md files found in {input_directory}")
        return
    
    with open(output_file, 'w', encoding='utf-8') as outfile:
        outfile.write("# MASTER INDEX\n\n")
        outfile.write(f"**Total Files Merged:** {len(md_files)}\n\n")
        outfile.write("---\n\n")
        
        # Write table of contents
        outfile.write("## 📑 TABLE OF CONTENTS\n\n")
        for idx, filepath in enumerate(md_files, 1):
            filename = os.path.basename(filepath)
            display_name = filename.replace('.md', '')
            outfile.write(f"{idx}. [{display_name}](#{display_name.lower().replace(' ', '-')})\n")
        
        outfile.write("\n---\n\n")
        
        # Write content
        for idx, filepath in enumerate(md_files, 1):
            filename = os.path.basename(filepath)
            display_name = filename.replace('.md', '')
            
            outfile.write(f"## {idx}. {display_name}\n\n")
            outfile.write(f"*Source: {filename}*\n\n")
            
            try:
                with open(filepath, 'r', encoding='utf-8') as infile:
                    content = infile.read()
                    outfile.write(content)
                    outfile.write("\n\n")
            except Exception as e:
                outfile.write(f"*Error reading file: {e}*\n\n")
            
            if idx < len(md_files):
                outfile.write("---\n\n")
    
    print(f"Successfully merged {len(md_files)} files into {output_file}")

def main():
    # Example usage 1: Simple merge of all .md files in current directory
    current_directory = "."  # Change this to your directory path
    merge_md_files(current_directory, "master_index.md")
    
    # Example usage 2: Merge with custom order (uncomment and modify as needed)
    # custom_file_order = [
    #     "introduction.md",
    #     "chapter1.md", 
    #     "chapter2.md",
    #     "conclusion.md"
    # ]
    # merge_with_custom_order(current_directory, "master_index.md", custom_file_order)
    
    # Example usage 3: Merge from specific directory
    # specific_directory = "/path/to/your/md/files"
    # merge_md_files(specific_directory, "master_index.md")

if __name__ == "__main__":
    main()