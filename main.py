import os
import shutil
import time
import zipfile
import platform

from nicegui import ui
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import config

# FRONTEND

# ------------------------------------------------------------------
# DATA
# ------------------------------------------------------------------
course_list = {
    779615: {
        "course_name": "FACC 300",
        "thumbnail_link": "https://s.brightspace.com/course-images/images/322cd582-6b20-4459-b7b9-1c92e9903c33/tile-low-density-max-size.jpg",
        "folders": {
            "Course Material": ["8286939", "8286940", "8286941"],
            "Course Notes": ["8286970"]
        }
    },
    762082: {
        "course_name": "ECSE 343",
        "thumbnail_link": "https://s.brightspace.com/course-images/images/bdcbbbed-ddab-4be9-8479-ee931512e3a0/tile-low-density-max-size.jpg",
        "folders": {
            "Course Outline": ["8267885"],
            "Lecture Schedule/Handouts": ["8268066"]
        }
    },
    # Add more courses as needed
}

# ------------------------------------------------------------------
# MEMORY
# ------------------------------------------------------------------
selected_courses = set()


# ------------------------------------------------------------------
# HELPER FUNCTIONS
# ------------------------------------------------------------------
def total_content_for_course(course_id) -> int:
    course = course_list[course_id]
    return sum(len(folder_content) for folder_content in course["folders"].values())


def total_selected_content() -> int:
    return sum(total_content_for_course(cid) for cid in selected_courses)


def update_status():
    ids_str = ", ".join(str(cid) for cid in selected_courses) if selected_courses else "None"
    status_label.text = (
        f"Selected courses: {ids_str}  |  "
        f"Total selected content: {total_selected_content()}"
    )
    download_button.text = f"Download {total_selected_content()} file(s)"


def toggle_selection(course_id, card_frame):
    if course_id in selected_courses:
        # Unselect
        selected_courses.remove(course_id)
        # Remove highlight styling
        card_frame.classes(remove="ring-4 ring-blue-500 shadow-xl")
    else:
        # Select
        selected_courses.add(course_id)
        # Add highlight styling
        card_frame.classes(add="ring-4 ring-blue-500 shadow-xl")
    update_status()

def download_files():
    os.mkdir("tmp")
    tmp_dir = os.getcwd()+"\\tmp"
    options = webdriver.ChromeOptions()
    prefs = {
        "download.default_directory": tmp_dir,
        "download.prompt_for_download": False,
        "directory_upgrade": True,
        "detach": True
    }
    options.add_experimental_option("prefs", prefs)  # Prevents the browser from closing automatically

    website = 'https://mycourses2.mcgill.ca/d2l/loginh/'
    path = config.driverPath
    service = Service(path)
    driver = webdriver.Chrome(service=service, options=options)
    driver.get(website)

    # Auto click the sign-in button
    sign_in_button = driver.find_element(By.XPATH,'//a[@id="link1"]')
    sign_in_button.click()

    # Wait for the initial shadow host
    host1 = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, "d2l-my-courses")))

    for cid, cinfo in course_list.items():
        for folders in cinfo["folders"].values():
            for file_id in folders:
                driver.get("https://mycourses2.mcgill.ca/d2l/le/content/"+str(cid)+"/topics/files/download/"+file_id+"/DirectFileTopicDownload")
                print(cid)

    while any([(filename.endswith(".crdownload") or filename.endswith(".tmp")) for filename in os.listdir(tmp_dir)]):
        time.sleep(0.1)

    downloads_folder = get_downloads_folder()
    zip_path = downloads_folder+"/combined_files.zip"  # Replace with the desired zip file path
    file_counter = 1

    while os.path.isfile(zip_path):
        zip_path = downloads_folder+"/combined_files ("+str(file_counter)+").zip"
        file_counter += 1

    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for file_name in os.listdir(tmp_dir):
            file_path = os.path.join(tmp_dir, file_name)
            zipf.write(file_path, os.path.basename(file_path))

    shutil.rmtree(tmp_dir)

    print(f"Files have been downloaded and zipped at {zip_path}")

def get_downloads_folder():
    if platform.system() == "Windows":
        return os.path.join(os.environ['USERPROFILE'], "Downloads")
    elif platform.system() == "Darwin":  # macOS
        return os.path.join(os.environ['HOME'], "Downloads")
    elif platform.system() == "Linux":
        return os.path.join(os.environ['HOME'], "Downloads")
    else:
        raise OSError("Unsupported Operating System")

# ------------------------------------------------------------------
# UI SETUP
# ------------------------------------------------------------------
# Create a header label to display current selections:
with ui.header().classes('justify-between items-center bg-gray-100 px-4 py-2 shadow'):
    ui.label("MyCourses Downloads").classes('text-2xl font-semibold text-black')

# Status label for tracking which courses (and how many contents) are selected:
status_label = ui.label("Selected courses: None | Total selected content: 0") \
    .classes('text-lg font-medium')

# Container for the course cards
with ui.row().classes('flex flex-wrap justify-center gap-6 p-4'):
    for course_id, course_info in course_list.items():
        # Pre-calculate the total content in each course
        content_count = total_content_for_course(course_id)

        with ui.card().classes('w-64 p-0 hover:shadow-lg transition-shadow cursor-pointer') as card_frame:
            with ui.element('div').classes('relative w-full h-40 overflow-hidden'):
                ui.image(course_info['thumbnail_link']) \
                    .classes('object-cover w-full h-full')

                with ui.element('div').classes(
                        'absolute top-0 left-0 m-2 px-3 py-1 bg-gray-800 bg-opacity-70 '
                        'text-white text-sm rounded'
                ):
                    ui.label(f"{content_count} file{'s' if content_count != 1 else ''}")

            ui.label(course_info['course_name']) \
                .classes('text-center text-lg font-semibold size-auto truncate pb-[16px] ml-[5px]')

            card_frame.on('click', lambda e, cid=course_id, cf=card_frame: toggle_selection(cid, cf))


# Footer with download button:
with ui.footer().classes('p-4'):
    download_button = ui.button(
        f"Download {total_selected_content()} file(s)",
        on_click=download_files
    ).props('color=primary')

if __name__ == "__main__":
    update_status()  # Make sure initial text is correct
    ui.run(title="MyCourses Downloads", reload=False)
