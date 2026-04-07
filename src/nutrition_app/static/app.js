const resultNode = document.getElementById("result");
const apiKeyNode = document.getElementById("api-key");

const storedKey = window.localStorage.getItem("nutrition-api-key");
if (storedKey) {
  apiKeyNode.value = storedKey;
}

apiKeyNode?.addEventListener("change", () => {
  window.localStorage.setItem("nutrition-api-key", apiKeyNode.value.trim());
});

function headers() {
  const apiKey = apiKeyNode?.value?.trim();
  const base = {};
  if (apiKey) {
    base["X-API-Key"] = apiKey;
  }
  return base;
}

async function submitJson(formId, url, bodyBuilder) {
  const form = document.getElementById(formId);
  form?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const body = bodyBuilder(new FormData(form));
    resultNode.textContent = "Сохраняю...";
    try {
      const response = await fetch(url, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...headers(),
        },
        body: JSON.stringify(body),
      });
      const payload = await response.json();
      resultNode.textContent = JSON.stringify(payload, null, 2);
    } catch (error) {
      resultNode.textContent = String(error);
    }
  });
}

const mealForm = document.getElementById("meal-form");
mealForm?.addEventListener("submit", async (event) => {
  event.preventDefault();
  resultNode.textContent = "Анализирую фото...";
  try {
    const response = await fetch("/api/meals/photo", {
      method: "POST",
      headers: headers(),
      body: new FormData(mealForm),
    });
    const payload = await response.json();
    resultNode.textContent = JSON.stringify(payload, null, 2);
  } catch (error) {
    resultNode.textContent = String(error);
  }
});

submitJson("weight-form", "/api/weights", (formData) => ({
  weight_kg: Number(formData.get("weight_kg")),
  note: formData.get("note") || null,
}));

submitJson("workout-form", "/api/workouts", (formData) => ({
  description: formData.get("description"),
  duration_min: formData.get("duration_min") ? Number(formData.get("duration_min")) : null,
  calories_burned: Number(formData.get("calories_burned")),
  avg_hr: formData.get("avg_hr") ? Number(formData.get("avg_hr")) : null,
  note: formData.get("note") || null,
}));
