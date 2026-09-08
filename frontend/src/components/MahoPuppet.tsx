import {
  forwardRef,
  useEffect,
  useImperativeHandle,
  useRef,
  useState,
} from "react";

import type { OverlayCharacterHandle } from "../overlayCharacter";
import type { MeshSpec } from "../maho/buildMesh";
import { SpeechPlayer } from "../audio/SpeechPlayer";
import { MahoMeshPlayer } from "../maho/meshPlayer";
import { MahoMotion } from "../maho/motion";
import { MouthDriver } from "../maho/viseme";

type Props = {
  onBusyChange?: (busy: boolean) => void;
};

const MahoPuppet = forwardRef<OverlayCharacterHandle, Props>(
  function MahoPuppet({ onBusyChange }, ref) {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const motionRef = useRef(new MahoMotion());
    const playerRef = useRef<MahoMeshPlayer | null>(null);
    const speechRef = useRef<SpeechPlayer | null>(null);
    const mouthRef = useRef(new MouthDriver());
    const onBusyRef = useRef(onBusyChange);
    const angerRef = useRef(false);
    const [anger, setAnger] = useState(false);
    onBusyRef.current = onBusyChange;

    useImperativeHandle(ref, () => ({
      playMotion(group: string) {
        const result = motionRef.current.play(group);
        if (result === "started") onBusyRef.current?.(true);
        return result;
      },
      hitTest(clientX: number, clientY: number) {
        const canvas = canvasRef.current;
        const player = playerRef.current;
        if (!canvas || !player) return false;
        const rect = canvas.getBoundingClientRect();
        if (rect.width <= 0 || rect.height <= 0) return false;
        const x = Math.floor((clientX - rect.left) * (canvas.width / rect.width));
        const y = Math.floor((rect.bottom - clientY) * (canvas.height / rect.height));
        if (x < 0 || y < 0 || x >= canvas.width || y >= canvas.height) return false;
        return player.hitTest(x, y);
      },
      setSleeping(sleeping: boolean) {
        if (sleeping) speechRef.current?.stop();
        motionRef.current.setSleeping(sleeping);
      },
      async prepareSpeech() {
        await speechRef.current?.prepare();
      },
      async playSpeech(url: string) {
        const speech = speechRef.current;
        if (!speech) return;
        onBusyRef.current?.(true);
        mouthRef.current.reset();
        motionRef.current.setSpeaking(true);
        try {
          await speech.play(url);
        } catch {
          motionRef.current.setSpeaking(false);
          onBusyRef.current?.(false);
        }
      },
      stopSpeech() {
        speechRef.current?.stop();
        motionRef.current.setSpeaking(false);
      },
    }), []);

    useEffect(() => {
      const canvas = canvasRef.current;
      if (!canvas) return;
      let destroyed = false;
      let frame = 0;
      let last = performance.now();
      const motion = motionRef.current;
      motion.onClipEnd = () => {
        if (speechRef.current?.isSpeaking()) return;
        onBusyRef.current?.(false);
      };
      const speech = new SpeechPlayer({
        onSpeakingChange(speaking) {
          motion.setSpeaking(speaking);
          if (!speaking) {
            mouthRef.current.reset();
            onBusyRef.current?.(false);
          }
        },
        onAmplitude(value) {
          motion.setMouth(mouthRef.current.viseme(value));
        },
      });
      speechRef.current = speech;

      const gl = canvas.getContext("webgl2", {
        alpha: true,
        premultipliedAlpha: true,
        antialias: false,
        preserveDrawingBuffer: true,
      });
      if (!gl) {
        speech.destroy();
        speechRef.current = null;
        return;
      }

      const resize = () => {
        const rect = canvas.getBoundingClientRect();
        const dpr = window.devicePixelRatio || 1;
        const width = Math.max(1, Math.floor(rect.width * dpr));
        const height = Math.max(1, Math.floor(rect.height * dpr));
        if (canvas.width !== width || canvas.height !== height) {
          canvas.width = width;
          canvas.height = height;
        }
        gl.viewport(0, 0, width, height);
      };

      resize();
      const observer = new ResizeObserver(resize);
      observer.observe(canvas);

      let player: MahoMeshPlayer | null = null;

      const render = () => {
        if (destroyed) return;
        const now = performance.now();
        const dt = Math.min((now - last) / 1000, 0.1);
        last = now;
        motion.update(dt);
        if (motion.angerMark !== angerRef.current) {
          angerRef.current = motion.angerMark;
          setAnger(motion.angerMark);
        }
        gl.viewport(0, 0, canvas.width, canvas.height);
        gl.clearColor(0, 0, 0, 0);
        gl.clear(gl.COLOR_BUFFER_BIT);
        player?.draw(motion.texture, {
          faceRot: motion.faceRot,
          hairSway: motion.hairSway,
          torsoBob: motion.torsoBob,
          armBob: motion.armBob,
          plushBob: motion.plushBob,
          shakeX: motion.shakeX,
        }, canvas.width, canvas.height);
        frame = requestAnimationFrame(render);
      };

      void (async () => {
        const spec = (await (await fetch("/maho/mesh.json")).json()) as MeshSpec;
        if (destroyed) return;
        player = new MahoMeshPlayer(gl, spec);
        playerRef.current = player;
        await player.initialize();
        if (destroyed) {
          player.destroy();
          return;
        }
        last = performance.now();
        render();
      })();

      return () => {
        destroyed = true;
        cancelAnimationFrame(frame);
        observer.disconnect();
        motion.onClipEnd = null;
        speech.destroy();
        speechRef.current = null;
        playerRef.current = null;
        player?.destroy();
      };
    }, []);

    return (
      <>
        <canvas ref={canvasRef} className="live2d-canvas" />
        <AngerMark visible={anger} />
      </>
    );
  },
);

function AngerMark({ visible }: { visible: boolean }) {
  return (
    <img
      src="/maho/anger-mark.svg"
      alt=""
      className={visible ? "anger-mark anger-mark-on" : "anger-mark"}
      draggable={false}
    />
  );
}

export default MahoPuppet;
