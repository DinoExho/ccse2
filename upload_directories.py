import os
import sys
import subprocess

def main():

    github_directory = sys.argv[1]
    username = sys.argv[2]
    api_token = sys.argv[3]
    upload_directory = sys.argv[4]

    for root, dirs, files in os.walk(github_directory):
        for file_name in files:

          full_github_path = os.path.join(root, file_name)
          
            curl_command = [
                "curl",
                "-X", "POST",
                "-H", f"Authorization: Token {api_token}",
                "-F", f"content=@{full_github_path}",
                f"https://www.pythonanywhere.com/api/v0/user/{username}/files/home/{USERNAME}/ccse2/{upload_directory}/{file_name}"
            ]

            try:
                result = subprocess.run(curl_command, capture_output=True, text=True, check=True)
            except subprocess.CalledProcessError as e:
                print(f"Failed to upload {file_name}")

if __name__ == "__main__":
    main()
