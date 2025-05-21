import os
import sys
import subprocess

def main():

    directory_path = sys.argv[1]
    username = sys.argv[2]
    api_token = sys.argv[3]
    github_workspace_path = sys.argv[4]
    print("entered python script")
    
    for root, dirs, files in os.walk(github_workspace_path):
        for file_name in files:
            full_github_path = os.path.join(root, file_name)
            curl_command = [
                "curl",
                "-X", "POST",
                "-H", f"Authorization: Token {api_token}",
                "-F", f"content=@{full_github_path}",
                f"https://www.pythonanywhere.com/api/v0/user/{username}/files/home/{username}/ccse2/{directory_path}/{file_name}"
            ]

            try:
                print(f"uploading")
                subprocess.run(curl_command, capture_output=True, text=True, check=True)
                
            except subprocess.CalledProcessError as e:
                print(f"Failed to upload {file_name}")

if __name__ == "__main__":
    main()
