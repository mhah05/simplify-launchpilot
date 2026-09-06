import os
import json
import base64
import boto3
from typing import List, Dict, Any, Literal
from typing_extensions import TypedDict
from pydantic import BaseModel, Field, field_validator
from dotenv import load_dotenv

# Import LangGraph classes for compiling the graph workflow
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langchain_aws import ChatBedrockConverse

load_dotenv()

# ==========================================
# 1. DEFINE PYDANTIC SCHEMAS (STRUCTURED OUTPUT)
# ==========================================
class RepoProfile(BaseModel):
    summary: str = Field(description="Plain-language summary of what the product actually does.")
    target_audience: str = Field(description="The primary target audience most likely to use this product.")
    tech_stack: List[str] = Field(description="List of primary libraries, languages, or tools discovered.")

    # DEFENSIVE COERCION: Coerces raw string descriptions back to a valid list structure
    @field_validator('tech_stack', mode='before')
    @classmethod
    def coerce_tech_stack(cls, v: Any) -> List[str]:
        if isinstance(v, str):
            return [v]
        return v

class CompetitorAnalysis(BaseModel):
    competitors: List[str] = Field(description="List of similar open-source or commercial products.")
    uniqueness: str = Field(description="The project's distinct angle and competitive differentiator.")

    @field_validator('competitors', mode='before')
    @classmethod
    def coerce_competitors(cls, v: Any) -> List[str]:
        if isinstance(v, str):
            return [v]
        return v

class MarketingStrategy(BaseModel):
    pillars: List[str] = Field(description="Pillars or content buckets (e.g., 'build in public', 'deep-dives').")
    cadence: str = Field(description="Weekly posting cadence (e.g., 3 posts a week).")

    @field_validator('pillars', mode='before')
    @classmethod
    def coerce_pillars(cls, v: Any) -> List[str]:
        if isinstance(v, str):
            return [v]
        return v

class SocialPost(BaseModel):
    post_id: int = Field(description="Unique ID of the post.")
    pillar: str = Field(description="The content pillar this post belongs to.")
    caption: str = Field(description="The social media caption text.")
    visual_prompt: str = Field(description="Prompt describing the graphic/visual to go with this post.")

class ContentCalendar(BaseModel):
    posts: List[SocialPost] = Field(description="A sequential list of drafted social posts.")

# ==========================================
# 2. DEFINE THE CENTRAL SHARED STATE
# ==========================================
class MarketingAppState(TypedDict):
    repo_raw_content: str               # The raw project code input
    repo_profile: Dict[str, Any]        # Step 1 (Extraction Profile)
    market_research: Dict[str, Any]     # Step 2 (OSINT competitor research)
    content_strategy: Dict[str, Any]    # Step 3 (High-level Marketing strategy)
    content_calendar: List[Dict[str, Any]] # Step 4 (Draft Timeline - 3 posts)
    published_file_paths: List[str]     # Tracks paths of generated image files
    is_post_approved: bool              # Human-in-the-loop flag
    current_post_index: int             # Tracks currently reviewed post
    loop_counter: int                   # Budget guard loop counter

# ==========================================
# 3. AWS / BEDROCK CLIENT INITIALIZATION
# ==========================================
llm = None
session = None
bedrock_runtime = None

def load_aws_credentials():
    """Initializes AWS Bedrock logical reasoning models and raw Titan Image Generation clients."""
    global llm, session, bedrock_runtime
    model_id = "anthropic.claude-3-haiku-20240307-v1:0"
    region_name = os.getenv("AWS_DEFAULT_REGION", "ap-southeast-1")

    llm = ChatBedrockConverse(
        model_id=model_id,
        temperature=0,  # Zero-temp guarantees stable output validation
        region_name=region_name
    )

    session = boto3.Session(profile_name=os.getenv("AWS_PROFILE", "workshop"))
    bedrock_runtime = session.client("bedrock-runtime", region_name=region_name)
    return llm, session, bedrock_runtime

# ==========================================
# 4. DEFINE WORKER NODES (READ -> WORK -> RETURN)
# ==========================================

# Step 1: Repo Analyst Agent (Extraction)
def repo_analyst_node(state: MarketingAppState) -> Dict[str, Any]:
    print("\n[Node 1] Running Repo Analyst Agent (Extraction)...")
    structured_llm = llm.with_structured_output(RepoProfile)
    prompt = f"Analyze this project description:\n\n{state['repo_raw_content']}"
    result = structured_llm.invoke(prompt)
    return {"repo_profile": result.model_dump()}

# Step 2: Market/Positioning Agent (OSINT Competitor Profiling)
def market_research_node(state: MarketingAppState) -> Dict[str, Any]:
    print("\n[Node 2] Running Market/Positioning Agent (Competitive Angle)...")
    structured_llm = llm.with_structured_output(CompetitorAnalysis)
    profile = state["repo_profile"]
    prompt = f"Find competitors and competitive edge for this project profile: {profile}"
    result = structured_llm.invoke(prompt)
    return {"market_research": result.model_dump()}

# Step 3: Marketing Strategist Node (Planning Strategy Guidelines)
def strategist_node(state: MarketingAppState) -> Dict[str, Any]:
    print("\n[Node 3] Running Marketing Strategist Node (Pillars & Cadence)...")
    structured_llm = llm.with_structured_output(MarketingStrategy)
    prompt = (
        f"Design marketing pillars and posting cadence. "
        f"Project: {state['repo_profile']}. Competitors: {state['market_research']}"
    )
    result = structured_llm.invoke(prompt)
    return {"content_strategy": result.model_dump()}

# Step 4: Content Creator Agent (Creative Calendar Drafting)
def content_creator_node(state: MarketingAppState) -> Dict[str, Any]:
    print("\n[Node 4] Running Content Creator Agent (Drafting Calendar Timeline)...")
    structured_llm = llm.with_structured_output(ContentCalendar)
    prompt = f"Create a timeline calendar of 3 posts mapping to this strategy: {state['content_strategy']}"
    result = structured_llm.invoke(prompt)
    return {
        "content_calendar": [post.model_dump() for post in result.posts],
        "current_post_index": 0,
        "published_file_paths": []
    }

# Step 5: Publishing Agent (Gated Transaction Node with Titan & Tweepy APIs)
def publish_post_node(state: MarketingAppState) -> Dict[str, Any]:
    idx = state["current_post_index"]
    posts = state["content_calendar"]
    paths = state.get("published_file_paths", [])

    if idx >= len(posts):
        print("\n❌ [ACTION GATED] Index out of calendar range!")
        return {}

    if not state["is_post_approved"]:
        print("\n❌ [ACTION GATED] Post not approved by user yet!")
        return {}

    post_to_publish = posts[idx]
    post_id = post_to_publish["post_id"]
    visual_prompt = post_to_publish["visual_prompt"]
    caption = post_to_publish["caption"]

    # --- A. REAL BEDROCK IMAGE GENERATION ---
    print(f"\n📡 [Step A] Connecting to Bedrock Titan Image Generator...")
    image_filename = f"post_{post_id}_graphic.png"
    has_real_image = False

    try:
        body = json.dumps({
            "taskType": "TEXT_IMAGE",
            "textToImageParams": {
                "text": f"High quality social media marketing graphic for: {visual_prompt}"
            },
            "imageGenerationConfig": {
                "numberOfImages": 1,
                "height": 512,
                "width": 512,
                "cfgScale": 8.0,
                "seed": 42
            }
        })

        response = bedrock_runtime.invoke_model(
            body=body,
            modelId="amazon.titan-image-generator-v1",
            contentType="application/json",
            accept="application/json"
        )

        response_body = json.loads(response.get("body").read())
        images_list = response_body.get("images")
        base64_image = next(iter(images_list))
        image_bytes = base64.b64decode(base64_image)

        with open(image_filename, "wb") as f:
            f.write(image_bytes)
        print(f"🎨 [Image Created] Generated real graphic and saved as: '{image_filename}'")
        has_real_image = True

    except Exception as e:
        print(f"⚠️ [Image Generation Failed] Unable to invoke Titan: {str(e)}")
        has_real_image = False

    # --- B. DEMO PUBLISHING LEDGER ---
    # Keep the demo independent of live X credentials. This intentionally does
    # not send a request to X; it records the approved post in the local log.
    print("\n🐦 [Demo Mode] Recording a simulated X publish...")
    tweet_id = f"demo-{post_id:03d}"
    feed_log = "published_social_feed.txt"
    with open(feed_log, "a", encoding="utf-8") as f:
        f.write(f"=== PUBLISHED POST #{post_id} (SIMULATED DEMO) ===\n")
        f.write(f"Caption: '{caption}'\n")
        f.write(f"Attached Asset Path: ./{image_filename if has_real_image else '(not generated)'}\n")
        f.write("Status: DEMO PUBLISH COMPLETED — NOT SENT TO X\n")
        f.write(f"Demo Post ID: {tweet_id}\n\n")
    print(f"✅ DEMO SUCCESS! Post recorded in {feed_log}. Demo ID: {tweet_id}")

    paths.append(image_filename)
    return {
        "current_post_index": idx + 1,
        "is_post_approved": False,  # Reset approval flag back to False for safety
        "published_file_paths": paths,
        "loop_counter": state.get("loop_counter", 0) + 1
    }

# ==========================================
# 5. CONSTRUCT THE FLOW GRAPH
# ==========================================
builder = StateGraph(MarketingAppState)

builder.add_node("repo_analyst", repo_analyst_node)
builder.add_node("market_research", market_research_node)
builder.add_node("strategist", strategist_node)
builder.add_node("content_creator", content_creator_node)
builder.add_node("publish_post", publish_post_node)

builder.add_edge(START, "repo_analyst")
builder.add_edge("repo_analyst", "market_research")
builder.add_edge("market_research", "strategist")
builder.add_edge("strategist", "content_creator")

def should_publish(state: MarketingAppState) -> Literal["publish_post", "__end__"]:
    idx = state.get("current_post_index", 0)
    calendar = state.get("content_calendar", [])
    loops = state.get("loop_counter", 0)

    print(f"Loop execution count: {loops}/5")
    if loops >= 5:
        print("[LOOP CAP ENFORCED] Hard termination triggered to protect AWS budget!")
        return END

    if idx < len(calendar):
        return "publish_post"
    return END

builder.add_conditional_edges("content_creator", should_publish)
builder.add_edge("publish_post", "content_creator")

memory = InMemorySaver()
compiled_graph = builder.compile(
    checkpointer=memory,
    interrupt_before=["publish_post"]
)
