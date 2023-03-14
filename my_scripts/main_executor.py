import os
import concurrent.futures

major_versions = ["ol6u6", "ol6u4", "ol6u8"]


def push_task(m_ver):
    os.system(f"python3 build_image.py --json on_prem.json --version {m_ver}")


if __name__ == '__main__':
    with concurrent.futures.ProcessPoolExecutor(max_workers=20) as executor:
        result = {executor.submit(push_task, m_ver): m_ver for m_ver in major_versions}


