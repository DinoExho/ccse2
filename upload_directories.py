import os
import sys
import subprocess

def main():

    directory_path = sys.argv[1]
    username = sys.argv[2]
    api_token = sys.argv[3]

    for root, dirs, files in os.walk(directory_path):
        for file_name in files:

            curl_command = [
                "curl",
                "-X", "POST",
                "-H", f"Authorization: Token {api_token}",
                "-F", f"content=@{directory_path}/{file_name}",
                f"https://www.pythonanywhere.com/api/v0/user/{username}/files/home/{username}/ccse2/{directory_path}/{file_name}"
            ]

            try:
                print(f"uploading")
                subprocess.run(curl_command, capture_output=True, text=True, check=True)
                
            except subprocess.CalledProcessError as e:
                print(f"Failed to upload {file_name}")

if __name__ == "__main__":
    main()
