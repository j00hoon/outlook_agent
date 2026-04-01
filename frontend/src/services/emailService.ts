// frontend/services/emailService.ts

const API_BASE_URL = "http://localhost:8001";

// Fetch available Outlook folders
export async function fetchFolders(): Promise<{ folders: string[] }> {
  const res = await fetch(`${API_BASE_URL}/emails/folders`);

  const text = await res.text();

  try {
    const data = JSON.parse(text);
    return {
      folders: Array.isArray(data.folders) ? data.folders : [],
    };
  } catch {
    console.error("Failed to parse folders:", text);
    return { folders: [] };
  }
}

// Fetch emails from a specific folder
export async function fetchEmails(folderName?: string) {
  const query = folderName ? `?folder=${encodeURIComponent(folderName)}` : "";

  const res = await fetch(`${API_BASE_URL}/emails/${query}`);

  const text = await res.text();

  try {
    const data = JSON.parse(text);

    if (Array.isArray(data.emails)) {
      return data.emails;
    }

    if (Array.isArray(data)) {
      return data;
    }

    return [];
  } catch {
    console.error("Failed to parse emails:", text);
    return [];
  }
}
