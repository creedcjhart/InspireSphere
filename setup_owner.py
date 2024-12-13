from app import app, create_owner_account

def setup():
    print("ReviewSphere Owner Account Setup")
    print("-" * 30)
    
    username = input("Enter owner username: ")
    email = input("Enter owner email: ")
    password = input("Enter owner password (min 8 characters): ")
    
    if len(password) < 8:
        print("Error: Password must be at least 8 characters long")
        return
    
    success, message = create_owner_account(username, email, password)
    print("\nResult:", message)

if __name__ == "__main__":
    setup()
