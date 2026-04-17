from deepface import DeepFace

def recognize_faces(img_path):
    dfs = DeepFace.find(
        img_path=img_path,
        db_path="data/known_faces",
        enforce_detection=False
    )

    people = []

    for df in dfs:
        if not df.empty:
            # take best match (lowest distance)
            best_match = df.iloc[0]

            identity_path = best_match['identity']
            name = identity_path.split("\\")[-2]  # folder name

            people.append(name)
        else:
            people.append("Unknown")

    return people