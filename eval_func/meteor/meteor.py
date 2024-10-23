import subprocess
import threading

class Meteor:

    def __init__(self):
        self._start_meteor()

    def _start_meteor(self):
        self.meteor_cmd = ['java', '-jar', '-Xmx2G', 'meteor-1.5.jar', '-', '-', '-stdio', '-l', 'en', '-norm']
        self.meteor_p = subprocess.Popen(self.meteor_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, bufsize=1)
        self.lock = threading.Lock()

    def compute_score(self, gts, res, retries=3):
        scores = []
        eval_line = 'EVAL'
        self.lock.acquire()
        for i in range(len(res)):
            assert (len(res[i]) == 1)
            stat = self._stat(res[i][0], gts[i])
            eval_line += ' ||| {}'.format(stat)

        try:
            self.meteor_p.stdin.write(eval_line + '\n')
        except BrokenPipeError as e:
            print(f"BrokenPipeError: {e}. Retrying...")
            self._restart_meteor_process()
            return self.compute_score(gts, res, retries - 1)  # Retry

        for i in range(len(res)):
            score = float(self.meteor_p.stdout.readline().strip())
            scores.append(score)

        final_score = float(self.meteor_p.stdout.readline().strip())
        self.lock.release()

        return final_score, scores

    def _restart_meteor_process(self):
        self.meteor_p.stdin.close()
        self.meteor_p.kill()
        self.meteor_p.wait()
        self._start_meteor()

    def method(self):
        return "METEOR"

    def _stat(self, hypothesis_str, reference_list):
        hypothesis_str = hypothesis_str.replace('|||', '').replace('  ', ' ')
        score_line = ' ||| '.join(('SCORE', ' ||| '.join(reference_list), hypothesis_str))
        self.meteor_p.stdin.write(score_line + '\n')
        return self.meteor_p.stdout.readline().strip()

    def __del__(self):
        self.lock.acquire()
        self.meteor_p.stdin.close()
        self.meteor_p.kill()
        self.meteor_p.wait()
        self.lock.release()
