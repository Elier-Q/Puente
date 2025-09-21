// app/hooks/uploadCamera.ts
import { BACKEND_URL } from "../constants/urls";

export async function uploadCamera(uri: string) {
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
      headers: {
        Accept: "application/json",
        // ⚠️ Don’t set Content-Type, fetch will do it for FormData
      },
    });

    if (!res.ok) throw new Error(`Server error: ${res.status}`);
    const data = await res.json();
    console.log("Translation response:", data);
    return data;
  } catch (err) {
    console.error("Upload error:", err);
    throw err;
  }
}
