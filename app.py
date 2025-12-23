import streamlit as st
import streamlit.components.v1 as components
import base64
import os

# 设置网页配置 (宽屏模式，体验更好)
st.set_page_config(layout="wide", page_title="小猫真棒 Streamlit版")

# ==========================================
# 1. 自动处理图片 (解决 Streamlit 找不到图片的问题)
# ==========================================
def get_image_base64(image_path):
    """把本地图片转成 Base64 字符串，嵌入 HTML"""
    if not os.path.exists(image_path):
        return None
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

# 读取你的猫咪图片
img_path = "mycat.png" 
img_base64 = get_image_base64(img_path)

# 如果没找到图片，给个提示，但防止报错
if img_base64:
    # 构造 Base64 格式的数据头
    img_src = f"data:image/png;base64,{img_base64}"
else:
    # 如果找不到图片，用个透明占位符或者网图
    img_src = "" 
    st.error("⚠️ 没找到 mycat.png！请确保图片和 app.py 在同一个文件夹。")


# ==========================================
# 2. 你的核心 HTML 代码
# ==========================================
# 注意：我们把之前的 './mycat.png' 替换成了 Python 变量 {img_src}
# 为了防止 Python 的 f-string 和 JS 的花括号冲突，我们使用 .replace 方法注入图片
# ==========================================

html_code = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        /* 稍微调整一下样式以适应 Streamlit 的 iframe */
        body { margin: 0; overflow: hidden; background-color: #f5f0e0; font-family: 'Segoe UI', sans-serif; }
        #container { position: absolute; top: 0; left: 0; width: 100%; height: 100%; z-index: 1; }
        
        /* 调试窗口 */
        #debug-container {
            position: absolute; top: 10px; left: 10px; width: 200px; height: 150px; z-index: 100;
            background: #000; border-radius: 10px; overflow: hidden; border: 2px solid rgba(255,255,255,0.5);
        }
        #input_video { position: absolute; width: 100%; height: 100%; object-fit: cover; opacity: 0.5; transform: scaleX(-1); }
        #output_canvas { position: absolute; width: 100%; height: 100%; transform: scaleX(-1); }
        #debug-text { position: absolute; bottom: 5px; left: 5px; color: #0f0; font-size: 10px; font-weight: bold; }

        /* 状态文字 */
        #status-message {
            position: absolute; top: 10%; left: 50%; transform: translateX(-50%);
            font-size: 24px; font-weight: 800; color: #444; background: rgba(255,255,255,0.95);
            padding: 15px 40px; border-radius: 40px; z-index: 50; text-align: center;
            box-shadow: 0 5px 20px rgba(0,0,0,0.1);
            width: 60%;
        }
        .sub-text { font-size: 14px; color: #666; display: block; margin-top: 5px;}
        .reward-mode { color: #E91E63 !important; border: 3px solid #E91E63; }

        /* 按钮 */
        #ui-controls {
            position: absolute; bottom: 20px; left: 50%; transform: translateX(-50%);
            display: flex; gap: 15px; z-index: 50; width: 90%; justify-content: center;
        }
        .game-btn {
            padding: 12px 20px; font-size: 16px; font-weight: bold; border: none; border-radius: 12px;
            color: white; cursor: pointer; box-shadow: 0 4px 0 rgba(0,0,0,0.2); flex: 1; max-width: 150px;
        }
        .game-btn:active { transform: translateY(4px); box-shadow: none; }
        .game-btn:disabled { opacity: 0.6; filter: grayscale(1); }
        #btn-carrot { background: linear-gradient(to bottom, #ff8a65, #ff5722); }
        #btn-glasses { background: linear-gradient(to bottom, #555, #222); }
        #btn-bottle { background: linear-gradient(to bottom, #42a5f5, #1565c0); }
    </style>
</head>
<body>

<div id="status-message">
    系统启动中...
    <span class="sub-text">Streamlit 版加载中</span>
</div>

<div id="debug-container">
    <video id="input_video" playsinline></video>
    <canvas id="output_canvas"></canvas>
    <div id="debug-text">AI 视觉: 待机</div>
</div>

<div id="container"></div>

<div id="ui-controls">
    <button id="btn-carrot" class="game-btn">🥕 胡萝卜</button>
    <button id="btn-glasses" class="game-btn">🕶️ 眼镜</button>
    <button id="btn-bottle" class="game-btn">💧 瓶子</button>
</div>

<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.9.1/gsap.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/@mediapipe/camera_utils/camera_utils.js" crossorigin="anonymous"></script>
<script src="https://cdn.jsdelivr.net/npm/@mediapipe/control_utils/control_utils.js" crossorigin="anonymous"></script>
<script src="https://cdn.jsdelivr.net/npm/@mediapipe/drawing_utils/drawing_utils.js" crossorigin="anonymous"></script>
<script src="https://cdn.jsdelivr.net/npm/@mediapipe/hands/hands.js" crossorigin="anonymous"></script>

<script>
    // --- 注入的图片数据 ---
    const CAT_IMAGE_SRC = "IMAGE_PLACEHOLDER"; // Python 会把这里替换掉

    let scene, camera, renderer, catGroup;
    let itemCarrot, itemGlasses, itemBottle;
    let isWaitingForReward = false;
    
    const statusMsg = document.getElementById('status-message');
    const debugText = document.getElementById('debug-text');
    const buttons = document.querySelectorAll('.game-btn');

    function enableShadows(group) {
        group.traverse((c) => { if(c.isMesh) { c.castShadow=true; c.receiveShadow=true; }});
    }

    function initThreeJS() {
        scene = new THREE.Scene();
        scene.background = new THREE.Color(0xf5f0e0);

        camera = new THREE.PerspectiveCamera(50, window.innerWidth / window.innerHeight, 0.1, 1000);
        camera.position.set(0, 3, 7);
        camera.lookAt(0, 1, 0);

        renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
        renderer.setSize(window.innerWidth, window.innerHeight);
        renderer.shadowMap.enabled = true;
        renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        document.getElementById('container').appendChild(renderer.domElement);

        const ambLight = new THREE.AmbientLight(0xffffff, 0.6);
        scene.add(ambLight);
        const dirLight = new THREE.DirectionalLight(0xffffff, 0.8);
        dirLight.position.set(5, 10, 5);
        dirLight.castShadow = true;
        scene.add(dirLight);

        const floor = new THREE.Mesh(new THREE.PlaneGeometry(30, 20), new THREE.ShadowMaterial({ opacity: 0.1 }));
        floor.rotation.x = -Math.PI / 2;
        floor.receiveShadow = true;
        scene.add(floor);

        createCatSprite();
        createProceduralItems();

        function animate() {
            requestAnimationFrame(animate);
            if(itemCarrot) itemCarrot.rotation.y += 0.005;
            if(itemGlasses) itemGlasses.rotation.y -= 0.005;
            if(itemBottle) itemBottle.rotation.y += 0.005;
            renderer.render(scene, camera);
        }
        animate();
        window.addEventListener('resize', () => {
            camera.aspect = window.innerWidth / window.innerHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(window.innerWidth, window.innerHeight);
        });
    }

    function createCatSprite() {
        catGroup = new THREE.Group();
        scene.add(catGroup);

        const loader = new THREE.TextureLoader();
        // 这里直接加载 Base64 图片数据
        loader.load(CAT_IMAGE_SRC, (texture) => {
            console.log("图片加载成功");
            const geometry = new THREE.PlaneGeometry(2.5, 3);
            const material = new THREE.MeshLambertMaterial({ map: texture, transparent: true, side: THREE.DoubleSide, alphaTest:0.5 });
            const catSprite = new THREE.Mesh(geometry, material);
            catSprite.position.y = 1.5;
            catSprite.castShadow = true;
            catGroup.add(catSprite);
        }, undefined, () => {
             console.error("图片加载失败");
             // 备用红方块
             const dummy = new THREE.Mesh(new THREE.BoxGeometry(1,1,1), new THREE.MeshBasicMaterial({color:0xff0000}));
             dummy.position.y = 1; catGroup.add(dummy);
        });
    }

    function createProceduralItems() {
        // 胡萝卜
        itemCarrot = new THREE.Group();
        const cBody = new THREE.Mesh(new THREE.CylinderGeometry(0.05, 0.3, 1.2, 16), new THREE.MeshLambertMaterial({ color: 0xff6b35 }));
        cBody.position.y = 0.6; itemCarrot.add(cBody);
        const leafGeo = new THREE.ConeGeometry(0.08, 0.4, 8);
        const leafMat = new THREE.MeshLambertMaterial({ color: 0x4CAF50 });
        for(let i=0; i<3; i++) {
            const l = new THREE.Mesh(leafGeo, leafMat);
            l.position.y = 1.2; l.rotation.z = (Math.random()-0.5)*0.5; itemCarrot.add(l);
        }
        itemCarrot.position.set(-2.5, 0, 2.5); enableShadows(itemCarrot); scene.add(itemCarrot);

        // 眼镜
        itemGlasses = new THREE.Group();
        const gMat = new THREE.MeshPhongMaterial({ color: 0x111111 });
        const rimGeo = new THREE.TorusGeometry(0.25, 0.04, 16, 32);
        const lRim = new THREE.Mesh(rimGeo, gMat); lRim.position.x = -0.35;
        const rRim = new THREE.Mesh(rimGeo, gMat); rRim.position.x = 0.35;
        const bridge = new THREE.Mesh(new THREE.BoxGeometry(0.2, 0.04, 0.04), gMat);
        itemGlasses.add(lRim, rRim, bridge);
        itemGlasses.position.set(0, 0.3, 2.5); enableShadows(itemGlasses); scene.add(itemGlasses);

        // 瓶子
        itemBottle = new THREE.Group();
        const bMat = new THREE.MeshPhongMaterial({ color: 0x2196F3, transparent: true, opacity: 0.7 });
        const bBody = new THREE.Mesh(new THREE.CylinderGeometry(0.3, 0.3, 0.8, 24), bMat); bBody.position.y = 0.4;
        const bCap = new THREE.Mesh(new THREE.CylinderGeometry(0.12, 0.12, 0.1, 24), new THREE.MeshLambertMaterial({color: 0xD32F2F})); bCap.position.y = 0.9;
        itemBottle.add(bBody, bCap);
        itemBottle.position.set(2.5, 0, 2.5); enableShadows(itemBottle); scene.add(itemBottle);
    }

    function handleSelection(type) {
        if(isWaitingForReward) return;
        buttons.forEach(b => b.disabled = true);
        
        let target, text;
        if(type==='carrot') { target=itemCarrot; text="胡萝卜"; }
        if(type==='glasses') { target=itemGlasses; text="眼镜"; }
        if(type==='bottle') { target=itemBottle; text="瓶子"; }

        statusMsg.innerHTML = `小猫选择 ${text}...`;
        statusMsg.classList.remove('reward-mode');

        const tl = gsap.timeline();
        tl.to(catGroup.rotation, { z: target.position.x * -0.08, x: 0.15, duration: 0.5 })
          .to(catGroup.position, { z: 1, duration: 0.5 }, "<")
          .to(target.position, { y: 1.0, duration: 0.2, yoyo: true, repeat: 1 }, "-=0.2")
          .call(() => {
              statusMsg.innerHTML = "🎉 选对啦！<br><span class='sub-text'>快伸手给摄像头喂食！</span>";
              statusMsg.classList.add('reward-mode');
              isWaitingForReward = true;
              debugText.innerText = "AI: 等待手掌..."; debugText.style.color = "#ffff00";
          })
          .to(catGroup.rotation, { z: 0, x: 0, duration: 0.5 })
          .to(catGroup.position, { z: 0, duration: 0.5 }, "<");
    }

    document.getElementById('btn-carrot').addEventListener('click', () => handleSelection('carrot'));
    document.getElementById('btn-glasses').addEventListener('click', () => handleSelection('glasses'));
    document.getElementById('btn-bottle').addEventListener('click', () => handleSelection('bottle'));

    // MediaPipe
    const videoElement = document.getElementById('input_video');
    const canvasElement = document.getElementById('output_canvas');
    const canvasCtx = canvasElement.getContext('2d');

    function onHandsResults(results) {
        canvasCtx.save();
        canvasCtx.clearRect(0, 0, canvasElement.width, canvasElement.height);
        if (results.multiHandLandmarks && results.multiHandLandmarks.length > 0) {
            for (const landmarks of results.multiHandLandmarks) {
                drawConnectors(canvasCtx, landmarks, HAND_CONNECTIONS, {color: '#00FF00', lineWidth: 2});
                drawLandmarks(canvasCtx, landmarks, {color: '#FF0000', lineWidth: 1});
            }
            if (isWaitingForReward) triggerReward();
        }
        canvasCtx.restore();
    }

    function triggerReward() {
        isWaitingForReward = false;
        debugText.innerText = "AI: 奖励触发!"; debugText.style.color = "#00ff00";
        statusMsg.innerHTML = "❤️ 小猫吃到奖励好开心！ ❤️";
        
        const tl = gsap.timeline();
        tl.to(catGroup.position, { y: 2.2, duration: 0.3, yoyo: true, repeat: 1 })
          .to(catGroup.rotation, { z: 0.2, duration: 0.1, yoyo: true, repeat: 5 }, "-=0.4")
          .call(() => {
              buttons.forEach(b => b.disabled = false);
              statusMsg.classList.remove('reward-mode');
              statusMsg.innerHTML = "请选择下一个物品";
          });
    }

    const hands = new Hands({locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/hands/${file}`});
    hands.setOptions({ maxNumHands: 1, modelComplexity: 0, minDetectionConfidence: 0.5, minTrackingConfidence: 0.5 });
    hands.onResults(onHandsResults);

    const cameraMediapipe = new Camera(videoElement, {
        onFrame: async () => { await hands.send({image: videoElement}); },
        width: 320, height: 240
    });
    cameraMediapipe.start().then(()=>statusMsg.innerHTML="系统就绪").catch(e=>statusMsg.innerHTML="摄像头未授权");

    initThreeJS();
</script>
</body>
</html>
"""

# ==========================================
# 3. 关键：注入图片数据并渲染
# ==========================================

# 把 Python 读取到的 Base64 图片替换到 HTML 字符串里的占位符
if img_src:
    final_html = html_code.replace("IMAGE_PLACEHOLDER", img_src)
else:
    # 没图片就只渲染代码，虽然猫会显示不出来
    final_html = html_code

# 在 Streamlit 中渲染 HTML
# height=800 保证显示区域足够大，scrolling=False 去掉滚动条
components.html(final_html, height=800, scrolling=False)