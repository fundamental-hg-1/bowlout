/* ==========================================================================
   Bowl Out Rice and Noodles — Menu Filtering & Order Redirect Modal
   ========================================================================== */

// Third-party ordering portal URL (update slug when Liberty Collective portal link is live)
const ORDER_PORTAL_URL = "https://www.meandu.app/liberty-collective-mvo/counter";

// Default menu dataset (overridden automatically if js/menu-data.js defines window.menuData)
const defaultBowlOutMenu = [
  // Appetizers
  {
    name: "Karaage",
    price: "$10",
    category: "appetizers",
    description: "Marinated fried chicken, spicy hoisin, sriracha aioli, cucumber, lime and togarashi."
  },
  {
    name: "Crab Rangoons (5pc)",
    price: "$10",
    category: "appetizers",
    description: "Cream cheese, imitation crab, green onions. Served with sweet chili sauce."
  },
  {
    name: "Pork Eggroll",
    price: "$3",
    category: "appetizers",
    description: "Served with sweet chili sauce."
  },
  {
    name: "Vegetable Spring Roll (2pc)",
    price: "$3",
    category: "appetizers",
    description: "Served with sweet chili sauce."
  },
  {
    name: "Pork Dumplings (5pc)",
    price: "$8",
    category: "appetizers",
    description: "Served with Soy Vinaigrette."
  },
  {
    name: "Edamame Salad",
    price: "$5",
    category: "appetizers",
    description: ""
  },
  {
    name: "Seaweed Salad",
    price: "$5",
    category: "appetizers",
    description: ""
  },

  // Ramens
  {
    name: "*Pork Belly Miso Ramen",
    price: "$16",
    category: "ramens",
    description: "Pork miso broth, menma, shiitake mushroom, soft-boiled egg, and green onion."
  },
  {
    name: "*Lemongrass Chicken Shoyu Ramen",
    price: "$15",
    category: "ramens",
    description: "Savory chicken shoyu broth, shiitake mushroom, soft-boiled egg, fried onion and green onion."
  },
  {
    name: "*Pork & Shrimp Wonton Shoyu Ramen",
    price: "$16",
    category: "ramens",
    description: "Savory chicken shoyu broth, wontons, shiitake mushroom, soft-boiled egg, and green onion."
  },

  // Rice Bowls
  {
    name: "*Pork Belly",
    price: "$16",
    category: "rice bowls",
    description: "Pork belly, cucumber, shiitake mushroom, avocado, soft-boiled egg, green onions, sesame seeds and spicy hoisin."
  },
  {
    name: "Chicken Karaage",
    price: "$14",
    category: "rice bowls",
    description: "Marinated fried chicken, seaweed, carrots, green onion, spicy hoisin and garlic sriracha aioli."
  },
  {
    name: "General Tso’s Chicken",
    price: "$14",
    category: "rice bowls",
    description: "Flash fried chicken thigh, broccoli, green onion and sesame seeds."
  },
  {
    name: "Teriyaki Chicken",
    price: "$14",
    category: "rice bowls",
    description: "Broccoli, carrots, mushrooms, sesame seeds and green onion."
  },
  {
    name: "Teriyaki Salmon",
    price: "$18",
    category: "rice bowls",
    description: "Broccoli, carrots, mushrooms, sesame seeds and green onion."
  },
  {
    name: "Poke",
    price: "$18",
    category: "rice bowls",
    description: "Choice of tuna or salmon, edamame pods, seaweed salad, avocado, cucumber and shredded carrots with spicy mayo."
  },

  // Kids Meals
  {
    name: "General Chicken",
    price: "$9",
    category: "kids meals",
    description: "Flash fried chicken thigh, broccoli, green onion and sesame seeds."
  },
  {
    name: "*Chicken Shoyu Ramen",
    price: "$9",
    category: "kids meals",
    description: "Savory chicken shoyu broth, shiitake mushroom, soft-boiled egg, fried onion and green onion."
  },
  {
    name: "Karaage w/ Rice",
    price: "$9",
    category: "kids meals",
    description: "Marinated fried chicken, seaweed, carrots, green onion, spicy hoisin and garlic sriracha aioli."
  }
];

function getActiveMenuItems() {
  if (Array.isArray(window.menuData) && window.menuData.length > 0) {
    return window.menuData;
  }
  return defaultBowlOutMenu;
}

function renderMenu(category = "all") {
  const container = document.getElementById("menu-container");
  if (!container) return;

  const items = getActiveMenuItems();
  const filtered =
    category === "all"
      ? items
      : items.filter((item) => item.category.toLowerCase() === category.toLowerCase());

  container.innerHTML = filtered
    .map(
      (item) => `
      <article class="menu-card">
        <div>
          <div class="menu-card-header">
            <h3>${item.name}</h3>
            <span class="menu-price">${item.price}</span>
          </div>
          ${item.description ? `<p>${item.description}</p>` : ""}
        </div>
        <span class="menu-tag">${item.category}</span>
      </article>
    `
    )
    .join("");
}

function filterMenu(category, buttonEl) {
  const filterButtons = document.querySelectorAll(".filters button");
  filterButtons.forEach((btn) => btn.classList.remove("active"));
  if (buttonEl) {
    buttonEl.classList.add("active");
  }
  renderMenu(category);
}

function renderConsumerAdvisory() {
  const upgradeContainer = document.getElementById("upgrade-container");
  if (!upgradeContainer) return;

  upgradeContainer.innerHTML = `
    <div class="menu-advisory">
      <strong>*Consumer Advisory:</strong> Consuming raw or undercooked meats, poultry, seafood, shellfish, or eggs may increase your risk of foodborne illness.
    </div>
  `;
}

document.addEventListener("DOMContentLoaded", () => {
  // 1. Initialize Menu & Consumer Advisory
  renderMenu("all");
  renderConsumerAdvisory();

  // 2. Order Online External Redirect Modal
  const orderModal = document.getElementById("orderModal");
  const orderTriggers = document.querySelectorAll(".order-trigger");
  const proceedBtn = document.getElementById("proceedBtn");
  const cancelBtn = document.getElementById("cancelBtn");

  function openOrderModal() {
    if (orderModal) {
      orderModal.classList.add("active");
    }
  }

  function closeOrderModal() {
    if (orderModal) {
      orderModal.classList.remove("active");
    }
  }

  orderTriggers.forEach((trigger) => {
    trigger.addEventListener("click", (e) => {
      e.preventDefault();
      openOrderModal();
    });
  });

  if (proceedBtn) {
    proceedBtn.addEventListener("click", () => {
      closeOrderModal();
      window.open(ORDER_PORTAL_URL, "_blank", "noopener,noreferrer");
    });
  }

  if (cancelBtn) {
    cancelBtn.addEventListener("click", closeOrderModal);
  }

  // Close modal when clicking outside the white dialog box
  if (orderModal) {
    orderModal.addEventListener("click", (e) => {
      if (e.target === orderModal) {
        closeOrderModal();
      }
    });
  }

  // Close modal when pressing Escape
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && orderModal && orderModal.classList.contains("active")) {
      closeOrderModal();
    }
  });
});