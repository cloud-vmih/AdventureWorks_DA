import subprocess
import sys
import os

def main():
    # Make sure we add Project2 to pythonpath
    my_env = os.environ.copy()
    my_env["PYTHONPATH"] = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    
    scripts = [
        "superset_bootstrap/bootstrap_chapter_1_business_health.py",
        "superset_bootstrap/bootstrap_chapter_2_growth_sources.py",
        "superset_bootstrap/bootstrap_chapter_3_sustainable_growth.py",
        "superset_bootstrap/bootstrap_chapter_4_product_value.py",
        "superset_bootstrap/bootstrap_chapter_5_macro_behavior.py"
    ]
    
    for script in scripts:
        print(f"\n==============================================")
        print(f"=== RUNNING BOOTSTRAP SCRIPT: {script} ===")
        print(f"==============================================")
        res = subprocess.run([sys.executable, script], env=my_env)
        if res.returncode != 0:
            print(f"\n[ERROR] Script {script} failed with exit code {res.returncode}")
            sys.exit(res.returncode)
            
    print("\n==============================================")
    print("=== ALL DASHBOARDS SUCCESSFULLY BOOTSTRAPPED ===")
    print("==============================================")

if __name__ == "__main__":
    main()
