import { CameraView, CameraType, useCameraPermissions } from "expo-camera";
import { useState, useRef } from "react";
import {
  Button,
  Text,
  StyleSheet,
  View,
  TouchableOpacity,
  Image,
} from "react-native";
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
        <Text style={styles.message}>
          We need your permission to show the camera
        </Text>
        <Button onPress={camRequestPermission} title="Grant permission" />
      </View>
    );
  }

  function toggleCameraFacing() {
    setFacing((current) => (current === "back" ? "front" : "back"));
  }

  // 📸 Take a picture
  async function takePicture() {
    if (!cameraRef.current) return;

    try {
      const photo = await cameraRef.current.takePictureAsync();
      setPhotoUri(photo.uri);
      await uploadPhoto(photo.uri);
    } catch (e) {
      console.warn("Failed to take picture", e);
    }
  }

  // 🖼️ Pick an image from gallery
  async function pickImage() {
    try {
      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: "images", // ✅ lowercase string
        allowsEditing: true,
        quality: 1,
      });

      if (!result.canceled) {
        const uri = result.assets[0].uri;
        setPhotoUri(uri);
        await uploadPhoto(uri);
      }
    } catch (e) {
      console.warn("Failed to pick image", e);
    }
  }

  // 🌐 Upload to backend
  async function uploadPhoto(photoUri: string) {
    try {
      const formData = new FormData();
      const fileExt = photoUri.split(".").pop() || "jpg";
      const fileType = fileExt === "heic" ? "image/heic" : "image/jpeg";

      formData.append("file", {
        uri: photoUri,
        name: `photo.${fileExt}`,
        type: fileType,
      } as any);

      const response = await fetch(`${BACKEND_URL}/translate-image`, {
        method: "POST",
        headers: {
          "Content-Type": "multipart/form-data",
        },
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Server error: ${response.status}`);
      }

      const data = await response.json();
      console.log("Upload success:", data);
    } catch (err) {
      console.error("Upload error:", err);
    }
  }

  return (
    <View style={styles.container}>
      <CameraView style={styles.camera} facing={facing} ref={cameraRef} />

      {/* Buttons */}
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

      {/* Preview of last photo */}
      {photoUri && (
        <View style={styles.previewContainer}>
          <Image source={{ uri: photoUri }} style={styles.preview} />
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, justifyContent: "center", backgroundColor: "#000" },
  message: { textAlign: "center", paddingBottom: 10, color: "#fff" },
  camera: { flex: 1 },
  buttonContainer: {
    position: "absolute",
    bottom: 64,
    flexDirection: "row",
    backgroundColor: "transparent",
    width: "100%",
    paddingHorizontal: 16,
    justifyContent: "space-around",
  },
  button: { alignItems: "center" },
  text: { fontSize: 18, fontWeight: "bold", color: "white" },
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
