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
                process = subprocess.run(curl_command, capture_output=True, text=True, check=True)
                if process.returncode == 0:
                    print("SUCCESS:")
                    if process.stdout:
                        print(process.stdout.strip())
                else:
                    print("FAIL")
                    if process.stdout:
                        print(process.stdout.strip())
                    if process.stderr:
                        print(process.stderr.strip())
                
            except subprocess.CalledProcessError as e:
                print(f"Failed to upload {file_name}")

if __name__ == "__main__":
    main()
