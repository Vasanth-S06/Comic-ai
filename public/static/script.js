const form = document.getElementById("comicForm");
const preview = document.getElementById("comicPreview");
const statusBox = document.getElementById("status");
const generateBtn = document.getElementById("generateBtn");
const downloadBtn = document.getElementById("downloadBtn");

let currentComic = null;

function renderComic(data) {
  preview.innerHTML = "";

  data.panels.forEach((panel, index) => {
    const card = document.createElement("article");
    card.className = "panel";

    const img = document.createElement("img");
    img.src = panel.image_url;
    img.alt = `Comic panel ${index + 1}`;

    const body = document.createElement("div");
    body.className = "panel-body";

    const title = document.createElement("h3");
    title.textContent = `Panel ${index + 1}: ${panel.title}`;

    const narration = document.createElement("div");
    narration.className = "narration";
    narration.textContent = panel.narration;

    const dialogue = document.createElement("div");
    dialogue.className = "dialogue";
    dialogue.textContent = panel.dialogue;

    body.append(title, narration, dialogue);
    card.append(img, body);
    preview.appendChild(card);
  });
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  generateBtn.disabled = true;
  downloadBtn.disabled = true;
  statusBox.textContent = "Generating story and images... This may take some time.";

  try {
    const response = await fetch("/api/generate", {
      method: "POST",
      body: new FormData(form)
    });

    const data = await response.json().catch(() => ({
      error: "The server took too long or returned an error. Please try again with fewer panels."
    }));

    if (!response.ok || data.error) {
      throw new Error(data.error || "Comic generation failed.");
    }

    currentComic = data;
    renderComic(data);
    downloadBtn.disabled = false;
    statusBox.textContent = data.notice || "Comic generated successfully.";
  } catch (error) {
    statusBox.textContent = error.message;
  } finally {
    generateBtn.disabled = false;
  }
});

downloadBtn.addEventListener("click", async () => {
  if (!currentComic) return;

  downloadBtn.disabled = true;
  statusBox.textContent = "Creating PDF...";

  try {
    const response = await fetch("/api/export", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        comic_id: currentComic.comic_id,
        title: currentComic.title,
        panels: currentComic.panels
      })
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.error || "PDF export failed.");
    }

    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `ComicCraft_${currentComic.comic_id}.pdf`;
    a.click();
    URL.revokeObjectURL(url);

    statusBox.textContent = "PDF exported successfully.";
  } catch (error) {
    statusBox.textContent = error.message;
  } finally {
    downloadBtn.disabled = false;
  }
});
