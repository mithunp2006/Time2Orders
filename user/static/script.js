function togglePincodeInput() {
  const dropdown = document.getElementById("pincodeDropdown");
  dropdown.style.display = dropdown.style.display === "block" ? "none" : "block";
}

function submitPincodeForm() {
  const newPin = document.getElementById("pincodeInput").value;
  document.getElementById("locationText").textContent = `Pincode: ${newPin}`;
  return true; // allow form to submit
}
