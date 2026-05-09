from fastapi import FastAPI, HTTPException, Request, Body, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field
from typing import Literal, List, Optional
from datetime import datetime, timezone
import os
from supabase import create_client, Client


# --- CONFIGURATION ---
# These should be set as Environment Variables in Vercel/Production
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    # Fallback for local dev if needed, but in production these MUST be set
    print("Warning: SUPABASE_URL or SUPABASE_KEY not set. Check environment variables.")



app = FastAPI(title="Campus Lost & Found")

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- DATABASE ---
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# --- MODELS ---
class ItemIn(BaseModel):
    name: str
    description: str
    location: str
    type: Literal["lost", "found"]
    contact: Optional[str] = None
    category: Optional[str] = None

# --- API ENDPOINTS ---

@app.post("/items", status_code=201)
def create_item(item: ItemIn):
    item_dict = item.dict()
    item_dict.update({
        "resolved": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    try:
        response = supabase.table("items").insert(item_dict).execute()
        return JSONResponse(status_code=201, content=response.data[0])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/items")
def get_items():
    try:
        response = supabase.table("items").select("*").order("created_at", desc=True).execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.patch("/items/{item_id}")
def resolve_item(item_id: int):
    try:
        response = supabase.table("items").update({"resolved": True}).eq("id", item_id).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Item not found")
            
        return response.data[0]
    except Exception as e:
        if isinstance(e, HTTPException): raise e
        raise HTTPException(status_code=500, detail=str(e))


# --- FRONTEND ---

HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Campus Lost & Found</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&family=Playfair+Display:wght@700&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>

    <style>
        :root {
            --bg-color: #0D0F14;
            --glass-bg: rgba(30, 34, 48, 0.7);
            --glass-border: rgba(255, 255, 255, 0.08);
            --accent-purple: #6C63FF;
            --accent-teal: #00D4AA;
            --text-main: #FFFFFF;
            --text-muted: #A0A0A0;
            --electronics: #6C63FF;
            --id-cards: #F59E0B;
            --clothing: #EC4899;
            --accessories: #8B5CF6;
            --books: #3B82F6;
            --other: #6B7280;
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'DM Sans', sans-serif;
        }

        body {
            background-color: var(--bg-color);
            color: var(--text-main);
            overflow-x: hidden;
            min-height: 100vh;
        }

        /* Animated Background Orbs */
        .orb {
            position: fixed;
            width: 600px;
            height: 600px;
            border-radius: 50%;
            filter: blur(120px);
            z-index: -1;
            opacity: 0.3;
            animation: drift 25s infinite alternate ease-in-out;
        }
        .orb-purple {
            background: radial-gradient(circle, var(--accent-purple), transparent);
            top: -200px;
            left: -200px;
        }
        .orb-teal {
            background: radial-gradient(circle, var(--accent-teal), transparent);
            bottom: -200px;
            right: -200px;
            animation-delay: -12s;
        }
        @keyframes drift {
            0% { transform: translate(0, 0) scale(1); }
            100% { transform: translate(150px, 100px) scale(1.1); }
        }

        /* Navbar */
        nav {
            position: sticky;
            top: 0;
            z-index: 100;
            background: rgba(13, 15, 20, 0.8);
            backdrop-filter: blur(10px);
            border-bottom: 1px solid var(--glass-border);
            padding: 1rem 2rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .logo {
            font-family: 'Playfair Display', serif;
            font-size: 1.5rem;
            font-weight: 700;
            background: linear-gradient(45deg, var(--accent-purple), var(--accent-teal));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .search-container {
            flex: 0 1 400px;
            position: relative;
        }

        .search-container input {
            width: 100%;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--glass-border);
            padding: 0.6rem 1rem;
            border-radius: 12px;
            color: white;
            outline: none;
            transition: 0.3s;
        }

        .search-container input:focus {
            border-color: var(--accent-purple);
            box-shadow: 0 0 15px rgba(108, 99, 255, 0.2);
        }

        .nav-badges {
            display: flex;
            gap: 1rem;
        }

        .badge {
            padding: 0.4rem 0.8rem;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .badge-lost { background: rgba(239, 68, 68, 0.2); color: #ef4444; border: 1px solid rgba(239, 68, 68, 0.3); }
        .badge-found { background: rgba(0, 212, 170, 0.2); color: var(--accent-teal); border: 1px solid rgba(0, 212, 170, 0.3); }

        /* Stats Bar */
        .stats-bar {
            background: rgba(255, 255, 255, 0.03);
            backdrop-filter: blur(10px);
            border-bottom: 1px solid var(--glass-border);
            padding: 1rem 2rem;
            display: flex;
            justify-content: space-around;
            text-align: center;
        }

        .stat-item h3 {
            font-size: 1.5rem;
            margin-bottom: 0.2rem;
        }

        .stat-item p {
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: var(--text-muted);
        }

        /* Main Grid */
        main {
            display: grid;
            grid-template-columns: 1fr 1.2fr 1fr;
            gap: 2rem;
            padding: 2rem;
            max-width: 1600px;
            margin: 0 auto;
        }

        @media (max-width: 1100px) {
            main { grid-template-columns: 1fr; }
        }

        /* Boards & Cards */
        .board-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 1.5rem;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid;
        }

        .lost-header { border-color: var(--accent-purple); color: var(--accent-purple); border-width: 3px; }
        .found-header { border-color: var(--accent-teal); color: var(--accent-teal); border-width: 3px; }


        .item-list {
            display: flex;
            flex-direction: column;
            gap: 1rem;
        }

        .glass-card {
            background: var(--glass-bg);
            backdrop-filter: blur(20px);
            border: 1px solid var(--glass-border);
            border-radius: 16px;
            padding: 1.5rem;
            transition: transform 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275), opacity 0.5s;
            animation: slideIn 0.5s ease forwards;
        }

        @keyframes slideIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .item-card {
            border-left: 4px solid transparent;
        }

        .item-card.lost { border-left-color: var(--accent-purple); }
        .item-card.found { border-left-color: var(--accent-teal); }

        .card-top {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 0.5rem;
        }

        .item-name {
            font-size: 1.3rem;
            font-weight: 700;
            color: white;
            letter-spacing: -0.02em;
        }

        .resolved .item-name { text-decoration: line-through; opacity: 0.5; }


        .time-ago {
            font-size: 0.75rem;
            color: var(--text-muted);
        }

        .location-pill {
            display: inline-block;
            padding: 0.2rem 0.6rem;
            border-radius: 10px;
            background: rgba(255, 255, 255, 0.05);
            font-size: 0.75rem;
            margin-bottom: 0.8rem;
        }

        .description {
            font-size: 0.9rem;
            color: #d1d1d1;
            margin-bottom: 1rem;
            line-height: 1.4;
        }

        .card-footer {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: 1rem;
        }

        .category-pill {
            padding: 0.2rem 0.6rem;
            border-radius: 6px;
            font-size: 0.7rem;
            font-weight: 700;
            text-transform: uppercase;
        }

        .btn-resolve {
            background: transparent;
            border: 1px solid rgba(255, 255, 255, 0.2);
            color: white;
            padding: 0.5rem 1rem;
            border-radius: 8px;
            cursor: pointer;
            width: 100%;
            margin-top: 1rem;
            transition: 0.3s;
        }

        .btn-resolve:hover {
            background: rgba(255, 255, 255, 0.1);
            border-color: white;
        }

        .resolved-banner {
            background: rgba(0, 212, 170, 0.15);
            color: var(--accent-teal);
            padding: 0.6rem;
            border-radius: 8px;
            text-align: center;
            font-weight: 700;
            margin-top: 1rem;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
        }

        /* Post Form */
        .post-form-card {
            position: sticky;
            top: 100px;
        }

        .type-toggle {
            display: flex;
            background: rgba(255, 255, 255, 0.05);
            padding: 0.3rem;
            border-radius: 12px;
            margin-bottom: 1.5rem;
        }

        .toggle-btn {
            flex: 1;
            padding: 0.8rem;
            border: none;
            border-radius: 10px;
            cursor: pointer;
            font-weight: 700;
            transition: 0.3s;
            background: transparent;
            color: var(--text-muted);
        }

        .toggle-btn.active.lost { background: var(--accent-purple); color: white; }
        .toggle-btn.active.found { background: var(--accent-teal); color: var(--bg-color); }

        .form-group {
            position: relative;
            margin-bottom: 1.5rem;
        }

        .form-group input, .form-group textarea, .form-group select {
            width: 100%;
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid var(--glass-border);
            padding: 0.8rem 1rem;
            border-radius: 10px;
            color: white;
            outline: none;
            transition: 0.3s;
        }

        .form-group label {
            position: absolute;
            left: 1rem;
            top: 0.8rem;
            color: var(--text-muted);
            pointer-events: none;
            transition: 0.3s;
        }

        .form-group input:focus ~ label,
        .form-group input:not(:placeholder-shown) ~ label,
        .form-group textarea:focus ~ label,
        .form-group textarea:not(:placeholder-shown) ~ label {
            top: -0.6rem;
            left: 0.8rem;
            font-size: 0.75rem;
            color: var(--accent-purple);
            background: var(--bg-color);
            padding: 0 0.4rem;
        }

        .form-group input:focus, .form-group textarea:focus {
            border-color: var(--accent-purple);
            box-shadow: 0 0 15px rgba(108, 99, 255, 0.1);
        }

        .btn-submit {
            width: 100%;
            padding: 1rem;
            border: none;
            border-radius: 12px;
            background: linear-gradient(45deg, var(--accent-purple), var(--accent-teal));
            color: white;
            font-weight: 700;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }

        .btn-submit:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(0, 0, 0, 0.3);
        }

        /* Toast Notifications */
        #toast-container {
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 1000;
            display: flex;
            flex-direction: column;
            gap: 10px;
        }

        .toast {
            min-width: 280px;
            padding: 1rem 1.5rem;
            background: rgba(20, 24, 35, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 12px;
            border-left: 5px solid;
            box-shadow: 0 10px 30px rgba(0,0,0,0.5);
            animation: slideInRight 0.3s ease forwards;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        @keyframes slideInRight {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }

        .toast.success { border-left-color: var(--accent-teal); }
        .toast.error { border-left-color: #ef4444; }
        .toast.info { border-left-color: var(--accent-purple); }

        /* Skeleton Loading */
        .skeleton {
            background: linear-gradient(90deg, rgba(255,255,255,0.05) 25%, rgba(255,255,255,0.1) 50%, rgba(255,255,255,0.05) 75%);
            background-size: 200% 100%;
            animation: shimmer 1.5s infinite;
        }

        @keyframes shimmer {
            0% { background-position: 200% 0; }
            100% { background-position: -200% 0; }
        }

        /* Empty State */
        .empty-state {
            text-align: center;
            padding: 3rem;
            opacity: 0.5;
        }
        .empty-state svg { width: 64px; height: 64px; margin-bottom: 1rem; fill: currentColor; }

        /* Form Error Shake */
        @keyframes shake {
            0%, 100% { transform: translateX(0); }
            25% { transform: translateX(-5px); }
            75% { transform: translateX(5px); }
        }
        .shake { animation: shake 0.3s; border-color: #ef4444 !important; }
        /* Auth Overlay */
        #auth-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: var(--bg-color);
            z-index: 1000;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: 0.5s;
        }

        .auth-card {
            width: 100%;
            max-width: 450px;
            padding: 3rem;
            text-align: center;
        }

        .auth-tabs {
            display: flex;
            gap: 1rem;
            margin-bottom: 2rem;
            border-bottom: 1px solid var(--glass-border);
        }

        .auth-tab {
            flex: 1;
            padding: 1rem;
            cursor: pointer;
            color: var(--text-muted);
            font-weight: 700;
            transition: 0.3s;
        }

        .auth-tab.active {
            color: var(--accent-purple);
            border-bottom: 2px solid var(--accent-purple);
        }

        .btn-google {
            width: 100%;
            padding: 0.8rem;
            background: white;
            color: black;
            border: none;
            border-radius: 10px;
            font-weight: 700;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
            margin-bottom: 1.5rem;
            cursor: pointer;
            transition: 0.3s;
        }

        .divider {
            margin: 1.5rem 0;
            display: flex;
            align-items: center;
            color: var(--text-muted);
            font-size: 0.8rem;
        }

        .divider::before, .divider::after {
            content: "";
            flex: 1;
            height: 1px;
            background: var(--glass-border);
            margin: 0 10px;
        }

        .forgot-link {
            display: block;
            margin-top: 1rem;
            color: var(--text-muted);
            font-size: 0.85rem;
            cursor: pointer;
            text-decoration: underline;
        }

        #app-content {
            display: none; /* Hidden until auth */
        }

        .user-profile {
            display: flex;
            align-items: center;
            gap: 0.8rem;
            background: rgba(255,255,255,0.05);
            padding: 0.5rem 1rem;
            border-radius: 12px;
            font-size: 0.9rem;
        }

        .btn-logout {
            background: rgba(239, 68, 68, 0.1);
            color: #ef4444;
            border: 1px solid rgba(239, 68, 68, 0.2);
            padding: 0.4rem 0.8rem;
            border-radius: 8px;
            cursor: pointer;
            font-size: 0.8rem;
        }
    </style>

</head>
<body>
    <div class="orb orb-purple"></div>
    <div class="orb orb-teal"></div>

    <div id="auth-overlay">
        <div class="glass-card auth-card">
            <div class="logo" style="font-size: 2.5rem; margin-bottom: 2rem;">CAMPUS FOUND</div>
            
            <div id="auth-main-view">
                <div class="auth-tabs">
                    <div class="auth-tab active" id="tab-login" onclick="toggleAuthMode('login')">Login</div>
                    <div class="auth-tab" id="tab-signup" onclick="toggleAuthMode('signup')">Sign Up</div>
                </div>

                <form id="authForm" onsubmit="event.preventDefault(); handleAuth();">
                    <div class="form-group">
                        <input type="email" id="authEmail" placeholder=" " required>
                        <label>College Email (.rvitm@rvei.edu.in)</label>
                    </div>
                    <div class="form-group">
                        <input type="password" id="authPassword" placeholder=" " required>
                        <label>Password</label>
                    </div>
                    <button type="submit" id="authSubmitBtn" class="btn-submit">LOGIN</button>
                </form>

                <p class="forgot-link" onclick="handleForgotPassword()">Forgot Password?</p>
            </div>


            <div id="auth-message-view" style="display: none;">
                <h3 id="auth-message-title">Check your email</h3>
                <p id="auth-message-text" style="color: var(--text-muted); margin: 1rem 0;"></p>
                <button class="btn-resolve" onclick="window.location.reload()">Back to Login</button>
            </div>
        </div>
    </div>

    <div id="app-content">
        <nav>
            <div class="logo">CAMPUS FOUND</div>
            <div class="search-container">
                <input type="text" id="searchInput" placeholder="Search by name, location or description..." onkeyup="filterItems()">
            </div>
            <div class="nav-badges" style="align-items: center;">
                <div class="user-profile">
                    <span id="user-display-name">User</span>
                    <button class="btn-logout" onclick="handleLogout()">Logout</button>
                </div>
                <div class="badge badge-lost"><span id="nav-lost-count">0</span> LOST</div>
                <div class="badge badge-found"><span id="nav-found-count">0</span> FOUND</div>
            </div>
        </nav>


    <div class="stats-bar">
        <div class="stat-item">
            <h3 id="stat-total">0</h3>
            <p>Total Posts</p>
        </div>
        <div class="stat-item">
            <h3 id="stat-open-lost">0</h3>
            <p>Open Lost</p>
        </div>
        <div class="stat-item">
            <h3 id="stat-resolved">0</h3>
            <p>Resolved</p>
        </div>
    </div>


    <main>
        <!-- Lost Board -->
        <section>
            <div class="board-header lost-header">
                <h2>LOST ITEMS</h2>
                <div class="badge badge-lost" id="lost-badge-count">0</div>
            </div>
            <div id="lost-board" class="item-list">
                <!-- Skeleton cards -->
                <div class="glass-card skeleton" style="height: 180px;"></div>
                <div class="glass-card skeleton" style="height: 180px;"></div>
            </div>
        </section>

        <!-- Post Form -->
        <section>
            <div class="glass-card post-form-card" id="form-card" style="border-color: var(--accent-purple);">
                <h2 id="form-title" style="margin-bottom: 1.5rem; text-align: center;">Report Lost Item</h2>

                <form id="postForm" onsubmit="event.preventDefault(); postItem();">

                    <div class="form-group">
                        <input type="text" id="itemName" placeholder=" " required>
                        <label>Item Name</label>
                    </div>
                    <div class="form-group">
                        <textarea id="itemDesc" placeholder=" " rows="3" required></textarea>
                        <label>Description</label>
                    </div>
                    <div class="form-group">
                        <input type="text" id="itemLoc" placeholder=" " required>
                        <label>Location</label>
                    </div>
                    <div class="form-group">
                        <input type="text" id="itemContact" placeholder=" ">
                        <label>Contact / WhatsApp (Optional)</label>
                    </div>
                    <div class="form-group">
                        <select id="itemCategory">
                            <option value="Other">Category: Other</option>
                            <option value="Electronics">Electronics</option>
                            <option value="ID/Cards">ID/Cards</option>
                            <option value="Clothing">Clothing</option>
                            <option value="Accessories">Accessories</option>
                            <option value="Books">Books</option>
                        </select>
                    </div>
                    <button type="submit" id="submit-btn" class="btn-submit">POST LOST ITEM</button>
                </form>
            </div>
        </section>


        <!-- Found Board -->
        <section>
            <div class="board-header found-header">
                <h2>FOUND ITEMS</h2>
                <div class="badge badge-found" id="found-badge-count">0</div>
            </div>
            <div id="found-board" class="item-list">
                <!-- Skeleton cards -->
                <div class="glass-card skeleton" style="height: 180px;"></div>
                <div class="glass-card skeleton" style="height: 180px;"></div>
            </div>
        </section>
        </main>
    </div>


    <div id="toast-container"></div>

    <script>
        let currentType = 'lost';
        let allItems = [];
        let isLoading = true;
        let authMode = 'login';
        let currentUser = null;

        // Initialize Supabase Auth
        async function checkUser() {
            const { data: { user } } = await _supabase.auth.getUser();
            if (user) {
                currentUser = user;
                onLoginSuccess(user);
            } else {
                document.getElementById('auth-overlay').style.display = 'flex';
                document.getElementById('app-content').style.display = 'none';
            }
        }

        // We use a prefixed name to avoid conflict with the backend 'supabase' object if any
        // but in JS, it's injected from the URL. Actually, the user already had supabase in JS?
        // Let's ensure _supabase is available.
        const _supabaseConfig = {
            url: "https://nrabaacyqmzqjlvsuumg.supabase.co",
            key: "sb_publishable_ybuBmAhGb7-kquI1-LpGPw_CWE_7ckl"
        };
        const _supabase = supabase.createClient(_supabaseConfig.url, _supabaseConfig.key);

        function toggleAuthMode(mode) {
            authMode = mode;
            document.getElementById('tab-login').classList.toggle('active', mode === 'login');
            document.getElementById('tab-signup').classList.toggle('active', mode === 'signup');
            document.getElementById('authSubmitBtn').innerText = mode === 'login' ? 'LOGIN' : 'CREATE ACCOUNT';
        }

        async function handleAuth() {
            const email = document.getElementById('authEmail').value;
            const password = document.getElementById('authPassword').value;

            // COLLEGE EMAIL VALIDATION
            if (!email.toLowerCase().endsWith('.rvitm@rvei.edu.in')) {
                showToast("Only college emails (.rvitm@rvei.edu.in) are allowed!", "error");
                return;
            }

            if (authMode === 'signup') {
                const { data, error } = await _supabase.auth.signUp({ email, password });
                if (error) return showToast(error.message, "error");
                
                document.getElementById('auth-main-view').style.display = 'none';
                document.getElementById('auth-message-view').style.display = 'block';
                document.getElementById('auth-message-text').innerText = "We've sent a verification link to your college email. Please verify to continue.";
            } else {
                const { data, error } = await _supabase.auth.signInWithPassword({ email, password });
                if (error) return showToast(error.message, "error");
                onLoginSuccess(data.user);
            }
        }

        async function handleForgotPassword() {

            const email = document.getElementById('authEmail').value;
            if (!email) return showToast("Enter your email first", "info");
            
            const { error } = await _supabase.auth.resetPasswordForEmail(email);
            if (error) showToast(error.message, "error");
            else showToast("Password reset link sent to your email!", "success");
        }

        function onLoginSuccess(user) {
            currentUser = user;
            const usn = user.email.split('.')[0].toUpperCase();
            document.getElementById('user-display-name').innerText = usn;
            document.getElementById('auth-overlay').style.opacity = '0';
            setTimeout(() => {
                document.getElementById('auth-overlay').style.display = 'none';
                document.getElementById('app-content').style.display = 'block';
                loadItems();
            }, 500);
        }

        async function handleLogout() {
            await _supabase.auth.signOut();
            window.location.reload();
        }

        const categoryColors = {
            'Electronics': '#6C63FF',
            'ID/Cards': '#F59E0B',
            'Clothing': '#EC4899',
            'Accessories': '#8B5CF6',
            'Books': '#3B82F6',
            'Other': '#6B7280'
        };

        // setFormType removed as form is now Lost only


        function timeAgo(date) {
            const seconds = Math.floor((new Date() - new Date(date)) / 1000);
            let interval = seconds / 31536000;
            if (interval > 1) return Math.floor(interval) + "y ago";
            interval = seconds / 2592000;
            if (interval > 1) return Math.floor(interval) + "mo ago";
            interval = seconds / 86400;
            if (interval > 1) return Math.floor(interval) + "d ago";
            interval = seconds / 3600;
            if (interval > 1) return Math.floor(interval) + "h ago";
            interval = seconds / 60;
            if (interval > 1) return Math.floor(interval) + "m ago";
            return Math.floor(seconds) + "s ago";
        }

        function animateValue(id, start, end, duration) {
            const obj = document.getElementById(id);
            if (!obj) return;
            let startTimestamp = null;
            const step = (timestamp) => {
                if (!startTimestamp) startTimestamp = timestamp;
                const progress = Math.min((timestamp - startTimestamp) / duration, 1);
                obj.innerText = Math.floor(progress * (end - start) + start);
                if (progress < 1) {
                    window.requestAnimationFrame(step);
                }
            };
            window.requestAnimationFrame(step);
        }

        function showToast(message, type = 'info') {
            const container = document.getElementById('toast-container');
            const toast = document.createElement('div');
            toast.className = `toast ${type}`;
            toast.innerHTML = `<span>${message}</span>`;
            container.appendChild(toast);
            setTimeout(() => {
                toast.style.opacity = '0';
                toast.style.transform = 'translateX(100%)';
                setTimeout(() => toast.remove(), 300);
            }, 3000);
        }

        async function loadItems() {
            try {
                const response = await fetch('/items');
                if (!response.ok) throw new Error('Fetch failed');
                allItems = await response.json();
                isLoading = false;
                renderBoards();
                updateStats();
            } catch (err) {
                console.error(err);
                showToast("Network error. Retrying...", "error");
            }
        }

        function renderBoards() {
            const lostBoard = document.getElementById('lost-board');
            const foundBoard = document.getElementById('found-board');
            
            if (isLoading) return; // Keep skeletons if still loading

            // Filter items: Lost board only shows unresolved lost items.
            // Found board shows all found items PLUS resolved lost items.
            const lostItems = allItems.filter(i => i.type === 'lost' && !i.resolved);
            const foundItems = allItems.filter(i => i.type === 'found' || (i.type === 'lost' && i.resolved));

            lostBoard.innerHTML = lostItems.length ? '' : createEmptyState('lost');
            foundBoard.innerHTML = foundItems.length ? '' : createEmptyState('found');

            lostItems.forEach(item => lostBoard.appendChild(createItemCard(item)));
            foundItems.forEach(item => foundBoard.appendChild(createItemCard(item)));

            document.getElementById('nav-lost-count').innerText = lostItems.length;
            document.getElementById('nav-found-count').innerText = foundItems.length;
            document.getElementById('lost-badge-count').innerText = lostItems.length;
            document.getElementById('found-badge-count').innerText = foundItems.length;

        }

        function createEmptyState(type) {
            return `
                <div class="empty-state">
                    <svg viewBox="0 0 24 24"><path d="M15.5,14L20.5,19L19,20.5L14,15.5V14.71L13.73,14.43C12.59,15.41 11.11,16 9.5,16A6.5,6.5 0 0,1 3,9.5A6.5,6.5 0 0,1 9.5,3A6.5,6.5 0 0,1 16,9.5C16,11.11 15.41,12.59 14.43,13.73L14.71,14H15.5M9.5,14C12,14 14,12 14,9.5C14,7 12,5 9.5,5C7,5 5,7 5,9.5C5,12 7,14 9.5,14Z"/></svg>
                    <p>No ${type} items yet</p>
                </div>
            `;
        }

        function createItemCard(item) {
            const card = document.createElement('div');
            card.className = `glass-card item-card ${item.type} ${item.resolved ? 'resolved' : ''}`;
            card.dataset.id = item.id;
            
            const catColor = categoryColors[item.category] || categoryColors['Other'];
            
            card.innerHTML = `
                <div class="card-top">
                    <span class="item-name">${item.name}</span>
                    <span class="time-ago">${timeAgo(item.created_at)}</span>
                </div>
                <div style="margin-bottom: 1rem; display: flex; flex-wrap: wrap; gap: 0.8rem; align-items: center;">
                    <span class="location-pill">📍 ${item.location}</span>
                    <span class="category-pill" style="background: ${catColor}20; color: ${catColor};">${item.category}</span>
                </div>

                <p class="description">${item.description}</p>
                ${item.contact ? `<p class="description" style="font-size: 0.85rem; color: var(--accent-teal); font-weight: 500;">📱 ${item.contact}</p>` : ''}
                
                ${item.resolved ? 
                    `<div class="resolved-banner" style="background: rgba(255,255,255,0.05); border: 1px solid var(--glass-border); color: var(--text-muted);">✓ Case Resolved</div>` : 
                    `<button class="btn-resolve" onclick="resolveItem('${item.id}')">Mark as Resolved</button>`
                }
            `;


            return card;
        }

        async function postItem() {
            const name = document.getElementById('itemName');
            const desc = document.getElementById('itemDesc');
            const loc = document.getElementById('itemLoc');
            const contact = document.getElementById('itemContact');
            const cat = document.getElementById('itemCategory');

            if (!name.value || !desc.value || !loc.value) {
                [name, desc, loc].forEach(el => { if(!el.value) el.parentElement.classList.add('shake'); });
                setTimeout(() => document.querySelectorAll('.shake').forEach(el => el.classList.remove('shake')), 500);
                showToast("Please fill in all required fields", "error");
                return;
            }

            const payload = {
                name: name.value,
                description: desc.value,
                location: loc.value,
                type: currentType,
                contact: contact.value || null,
                category: cat.value
            };

            try {
                const res = await fetch('/items', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                if (res.ok) {
                    showToast("Item posted successfully!", "success");
                    document.getElementById('postForm').reset();
                    loadItems();
                }
            } catch (err) {
                showToast("Failed to post item", "error");
            }
        }

        async function resolveItem(id) {
            try {
                const res = await fetch(`/items/${id}`, { method: 'PATCH' });
                if (res.ok) {
                    showToast("Item marked as resolved!", "success");
                    loadItems();
                }
            } catch (err) {
                showToast("Action failed", "error");
            }
        }

        function filterItems() {
            const query = document.getElementById('searchInput').value.toLowerCase();
            const cards = document.querySelectorAll('.item-card');
            let matchCount = 0;

            cards.forEach(card => {
                const text = card.innerText.toLowerCase();
                if (text.includes(query)) {
                    card.style.display = 'block';
                    matchCount++;
                } else {
                    card.style.display = 'none';
                }
            });
            
            // Handle no results message if needed
        }

        function updateStats() {
            const total = allItems.length;
            const openLost = allItems.filter(i => i.type === 'lost' && !i.resolved).length;
            const resolved = allItems.filter(i => i.resolved).length;

            const prevTotal = parseInt(document.getElementById('stat-total').innerText) || 0;
            const prevLost = parseInt(document.getElementById('stat-open-lost').innerText) || 0;
            const prevResolved = parseInt(document.getElementById('stat-resolved').innerText) || 0;

            animateValue('stat-total', prevTotal, total, 800);
            animateValue('stat-open-lost', prevLost, openLost, 800);
            animateValue('stat-resolved', prevResolved, resolved, 800);
        }


        document.addEventListener('DOMContentLoaded', () => {
            checkUser(); // Check auth first
            setInterval(loadItems, 30000); // Slower interval to be kind to Supabase
        });


    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def read_root():
    return HTML_PAGE

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
