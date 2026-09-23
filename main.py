import os
import base64
from fastapi import FastAPI, UploadFile, File, Form
from typing import List
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv

load_dotenv()
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")

model = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite", temperature=0)


class MahjongAction(BaseModel):
    is_defense_mode: bool = Field(description="Whether to initiate full defense mode based on enemy riichi status.")
    thinking: str = Field(
        description="Brief analysis of my hand tiles and the river safety (Keep it short and in English).")
    discard_tile: str = Field(description="The tile to discard, e.g., '1m', '5p', '南', '中'. Must be in my hand!")
    should_call: str = Field(description="Action to take: 'none', 'chi', 'pong', 'riichi', 'ron'")


structured_model = model.with_structured_output(MahjongAction, method="function_calling")

app = FastAPI(title="雀魂AI多图极速决策微服务")


@app.post("/analyze-board")
async def analyze_board(
        file_hand: UploadFile = File(...),
        file_center: UploadFile = File(...),
        file_dora: UploadFile = File(...),
        riichi_upstream: str = Form("false"),
        riichi_downstream: str = Form("false"),
        riichi_opposite: str = Form("false")
):
    """
    接收前台压缩后的『手牌特写』和『牌河中心特写』双图流
    """
    try:
        hand_bytes = await file_hand.read()
        center_bytes = await file_center.read()
        dora_bytes = await file_dora.read()

        url_hand = f"data:image/png;base64,{base64.b64encode(hand_bytes).decode('utf-8')}"
        url_center = f"data:image/png;base64,{base64.b64encode(center_bytes).decode('utf-8')}"
        url_dora = f"data:image/jpeg;base64,{base64.b64encode(dora_bytes).decode('utf-8')}"

        active_riichi_players = []
        if riichi_upstream == "true": active_riichi_players.append("左侧【上家】(Upstream)")
        if riichi_downstream == "true": active_riichi_players.append("右侧【下家】(Downstream)")
        if riichi_opposite == "true": active_riichi_players.append("上方【对家】(Opposite)")

        riichi_status_string = "、".join(active_riichi_players) if active_riichi_players else "暂无任何人立直"

        prompt_text = (
            "\"You are a legendary, super-defensive Japanese Mahjong (Riichi Mahjong) Grandmaster Agent. \"\n"
            "\"Your ultimate, unyielding goal is TOTAL DEFENSE to AVOID DEALING IN (放铳/点炮) at all costs, \"\n"
            "\"while accurately calculating value and read speed when the board is safe.\\n\\n\"\n\n"

            "\"🚨【LIVE RIICHI MILITARY STATUS / 实时立直军情】🚨\\n\"\n"
            f"\"- Current declared Riichi opponents: {riichi_status_string}\\n\"\n"
            f"\"- riichi_upstream = {riichi_upstream}, riichi_downstream = {riichi_downstream}, riichi_opposite = {riichi_opposite}\\n\\n\"\n\n"

            "\"📝【INPUT IMAGES】\\n\"\n"
            "\"1. Image 1: My EXACT current hand tiles. Your `discard_tile` MUST be chosen from these tiles only! No hallucinations!\\n\"\n"
            "\"2. Image 3: The Dora Indicator tiles row (宝牌指示牌跑道) containing up to 5 slots.\\n\"\n"
            "\"3. Image 2: The discard river (河) and central board status.\\n\\n\"\n\n"

            "\"🧠【STEP 1: UNIVERSAL DORA (宝牌) DYNAMIC CALCULATION】\\n\"\n"
            "\"Identify ALL active Dora Indicators from Image 3 and calculate the actual Dora tiles of this round:\\n\"\n"
            "\"🚨🚨🚨 MULTI-DORA & KAN COMPATIBLE RULES (多宝牌与开杠动态清点铁律) 🚨🚨🚨\\n\"\n"
            "\"1. Image 3 shows a horizontal row of 5 Dora Indicator slots from LEFT to RIGHT.\\n\"\n"
            "\"2. Active Indicators Check: Scan from the VERY LEFT slot to the right. Count EVERY tile that is turned FACE-UP (白底花纹面). Ignore the face-down orange tiles (牌背).\\n\"\n"
            "\"3. Multi-Dora Calculation: For EACH face-up tile you identified, apply the Indicator + 1 rule individually. All calculated tiles are active Doras simultaneously!\\n\"\n"
            "\"4. Suit Discrimination Rule for Face-up Tiles:\\n\"\n"
            "\"   - Bamboo sticks (索子/条子) = Sou (s) tile! (e.g., 6 vertical sticks = 6s, Dora is 7s).\\n\"\n"
            "\"   - Circular dots (饼子/筒子) = Pin (p) tile! (e.g., 6 dots = 6p, Dora is 7p).\\n\"\n"
            "\"   - Chinese characters (万/字牌) = Man (m) or Honor tile! (Do NOT confuse distorted Sou/Pin lines with Man characters!)\\n\"\n"
            "\"- Number Tiles (万/饼/条): The actual Dora is Indicator + 1 (e.g., 3p -> 4p, 9m -> 1m).\\n\"\n"
            "\"- Wind Tiles (字牌-风): 东 -> 南 -> 西 -> 北 -> 东 (e.g., if Indicator is 东, Dora is 南).\\n\"\n"
            "\"- Dragon Tiles (字牌-三元): 白(白) -> 发(发) -> 中(中) -> 白(白).\\n\"\n"
            "\"- Red Dora Check: Also look at Image 1. If any tile has a glowing bright red font (Red Dora/赤宝牌), it is automatically a Dora tile. \"\n"
            "\"All Dora tiles are worth +1 Han and should be preserved in early safe turns, but dynamically devalued or kept as defensive shields if dead/unsafe.\\n\\n\"\n\n"

            "\"🧠【STEP 2: OPPONENT HAND READING & ORDER ANALYSIS (早巡手顺读牌)】\\n\"\n"
            "\"Scan the sequence of tiles discarded by all opponents in Image 2 during the early game (Turns 1-6) to deduce their hand shapes, value, and speed before they declare Riichi.\\n\"\n"
            "\"1. ⚡ Standard Shape (标准高效攻型):\\n\"\n"
            "\"   - Early discards (Turns 1-3) consist strictly of isolated honors (字牌) or terminals (1, 9). This means their hand is highly efficient and moving at top speed.\\n\"\n"
            "\"2. 🚨 Value Shape / Hidden Threat (异常手顺/七对子/染手):\\n\"\n"
            "\"   - Early Mid-tile Discard (弃中张): If an opponent discards central tiles (4, 5, 6) in turns 1-3 while keeping honors, they are likely holding pairs (Chitoitsu) or a finished shape.\\n\"\n"
            "\"   - Reverse Order Discard (逆切): If they discard 5 then 4, or 7 then 6 in early turns, they have a surplus of connected blocks, meaning they are incredibly fast.\\n\\n\"\n\n"

            "\"🧠【STEP 3: DEFENSIVE TACTICS & SAFETY RANKING (铁壁防守算法)】\\n\"\n"
            "\"If any opponent declares Riichi (立直棒 extended), or it is Turn 7+ and your hand is slow/bad, you MUST enter FULL DEFENSE MODE (`is_defense_mode = true`).\\n\\n\"\n"
            "\"🚨🚨🚨 STATED DISCARD RIVER OWNERSHIP RULES (牌河绝对归属铁律) 🚨🚨🚨\\n\"\n"
            "\"When tracking Genbutsu (现物), you MUST strictly isolate tile ownership based on spatial position in Image 2:\\n\"\n"
            "\"1. THE BOTTOM RIVER IS YOUR OWN RIVER! Tiles in the bottom river were discarded by YOU. They are NEVER Genbutsu (现物) for any opponent! Do NOT recommend a tile just because you see it in the bottom river!\\n\"\n"
            "\"2. Only tiles physically located inside a specific opponent's river belong to that opponent. Cross-check with the 'LIVE RIICHI STATUS' above to identify exactly who is threatening you, and only read THAT threat's river for Genbutsu!\\n\\n\"\n"
            "\"1. 🛡️ Genbutsu (现物 - 100% Absolute Safe):\\n\"\n"
            "\"   - Tiles directly discarded by the SPECIFIC active Riichi player (as specified in LIVE RIICHI STATUS). Due to Furiten (振听), these can NEVER deal in. Prioritize these above all else.\\n\"\n"
            "\"2. 筋牌 (Suuji - Two-sided Wait Safety Rule):\\n\"\n"
            "\"   - If '4' is dead in the specific threat's river, check if '1' and '7' are safe against a two-sided wait. \\n\"\n"
            "\"   - If both '1' and '7' are dead, '4' becomes a 'Double Suuji' (双筋) and its danger level drops heavily.\\n\"\n"
            "\"   - Prioritize terminal Suuji (1, 9) over middle Suuji (4, 5, 6) as they cannot form sequential sets on both sides.\\n\"\n"
            "\"3. 壁牌 (Kabe - Blocked Wall End Rule):\\n\"\n"
            "\"   - Scan Image 2 (river + melds) for 'No-Suuji' or wall blocks. If all 4 copies of a specific number tile are visible (e.g., all four '8-Man' are dead), tiles beyond the wall (e.g., '9-Man') are safe from順子.\\n\"\n"
            "\"4. 早巡外露安全区 (Early Discard Slits):\\n\"\n"
            "\"   - Tiles close to an opponent's early discards (Turns 1-3, e.g., if early 1m, then 2m/3m) have a statistically lower probability of being targeted by them.\\n\\n\"\n\n"

            "\"🎯【FINAL ARBITRATION】\\n\"\n"
            "\"Output the optimal `discard_tile` using standard notation ('1m', '5p', '7s', '东', '南', '西', '北', '白', '发', '中'). \"\n"
            "\"In the `thinking` field, provide a concise tactical breakdown IN ENGLISH explaining:\\n\"\n"
            "\"1) Your dynamic Dora calculation and its visibility count.\\n\"\n"
            "\"2) What you read from opponents' early discard order (speed/shape).\\n\"\n"
            "\"3) Your explicit defensive justification (e.g., '打现物', '利用X筋牌', '依据X为壁牌防守').\\n\"\n"
            "\"⚠️ Crucial Check: Explicitly confirm in your text that the recommended safe tile is NOT chosen based on your own bottom river!\\n\"\n"
        )

        message = HumanMessage(
            content=[
                {"type": "text", "text": prompt_text},
                {"type": "image_url", "image_url": {"url": url_hand}},
                {"type": "image_url", "image_url": {"url": url_center}},
                {"type": "image_url", "image_url": {"url": url_dora}}
            ]
        )

        print("多图联合长考中...")
        decision = structured_model.invoke([message])

        return {"status": "success", "decision": decision.dict()}

    except Exception as e:
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)