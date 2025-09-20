import { CameraView, CameraType, useCameraPermissions } from "expo-camera";
import { useState, useRef } from "react";
import { View, Text, Button, TouchableOpacity, Image, StyleSheet } from "react-native";
import * as ImagePicker from "expo-image-picker";
import { BACKEND_URL } from "../../constants/urls";

export default function App() {
  const [facing, setFacing] = useState<CameraType>("back");
  const [permission, camRequestPermission] = useCameraPermissions();
  const [photoUri, setPhotoUri] = useState<string | null>(null);
  const cameraRef = useRef<CameraView | null>(null);

  if (!permission) return <View />;

  if (!permission.granted) {
    return (
      <View style={styles.container}>
        <Text style={styles.message}>Camera permission required</Text>
        <Button onPress={camRequestPermission} title="Grant permission" />
      </View>
    );
  }

  const toggleCameraFacing = () => {
    setFacing(facing === "back" ? "front" : "back");
  };

  const takePicture = async () => {
    if (!cameraRef.current) return;
    const photo = await cameraRef.current.takePictureAsync();
    setPhotoUri(photo.uri);
    await uploadPhoto(photo.uri);
  };

  const pickImage = async () => {
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images, // ✅ correct usage
      allowsEditing: true,
      quality: 1,
    });

    if (!result.canceled) {
      const uri = result.assets[0].uri;
      setPhotoUri(uri);
      await uploadPhoto(uri);
    }
  };

  const uploadPhoto = async (uri: string) => {
  try {
    const formData = new FormData();
    const ext = uri.split(".").pop() || "jpg";
    const type = ext === "heic" ? "image/heic" : "image/jpeg";

    formData.append("file", {
      uri,
      name: `photo.${ext}`,
      type,
    } as any);

    const res = await fetch(`${BACKEND_URL}/translate-image`, {
      method: "POST",
      body: formData,
      // ❌ Don't set Content-Type here
      headers: {
        Accept: "application/json",
      },
    });

    if (!res.ok) throw new Error(`Server error: ${res.status}`);
    const data = await res.json();
    console.log("Translation response:", data);
  } catch (err) {
    console.error("Upload error:", err);
  }
};


  return (
    <View style={styles.container}>
      <CameraView style={styles.camera} facing={facing} ref={cameraRef} />

      <View style={styles.buttonContainer}>
        <TouchableOpacity style={styles.button} onPress={toggleCameraFacing}>
          <Text style={styles.text}>Flip</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.button} onPress={takePicture}>
          <Text style={styles.text}>Snap</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.button} onPress={pickImage}>
          <Text style={styles.text}>Gallery</Text>
        </TouchableOpacity>
      </View>

      {photoUri && (
        <View style={styles.previewContainer}>
          <Image source={{ uri: photoUri }} style={styles.preview} />
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#000" },
  message: { textAlign: "center", padding: 10, color: "white" },
  camera: { flex: 1 },
  buttonContainer: {
    position: "absolute",
    bottom: 64,
    flexDirection: "row",
    justifyContent: "space-around",
    width: "100%",
    paddingHorizontal: 16,
  },
  button: { alignItems: "center" },
  text: { color: "white", fontSize: 18, fontWeight: "bold" },
  previewContainer: {
    position: "absolute",
    top: 64,
    right: 16,
    borderWidth: 2,
    borderColor: "white",
    borderRadius: 8,
    overflow: "hidden",
  },
  preview: { width: 100, height: 150 },
});
