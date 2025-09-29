def print_dog_groups(dog_groups):
    print("New:")
    for dog in dog_groups.get('new_dogs', []):
        name = dog.get('name', 'Unnamed Dog')
        url = dog.get('url', 'No URL')
        print(f"  {name} - {url}")
    print() # blank line 
    print("Returned:")
    for dog in dog_groups.get('returned_dogs', []):
        name = dog.get('name', 'Unnamed Dog')
        url = dog.get('url', 'No URL')
        print(f"  {name} - {url}")
    print() # blank line 
    print("Adopted/Reclaimed:")
    for dog in dog_groups.get('adopted_dogs', []):
        name = dog.get('name', 'Unnamed Dog')
        url = dog.get('url', 'No URL')
        print(f"  {name} - {url}")
    print()  

    print("Trial Adoptions:")
    for dog in dog_groups.get('trial_adoption_dogs', []):
        name = dog.get('name', 'Unnamed Dog')
        url = dog.get('url', 'No URL')
        print(f"  {name} - {url}")
    print()

    print("Available but Temporarily Unlisted:")
    for dog in dog_groups.get('other_unlisted_dogs', []):
        name = dog.get('name', 'Unnamed Dog')
        url = dog.get('url', 'No URL')
        print(f"  {name} - {url}")
    print()

