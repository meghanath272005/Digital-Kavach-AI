"""Hybrid scam check: transparent rules DECIDE 'High'. An optional ML model may raise a message to 'Medium' at most.

An ML model is used ONLY if a real trained model file exists (exported from the Colab notebook). If not,
the response says so plainly - nothing is faked.
"""
from . import scam_rules

ML_RAISE_THRESHOLD = 0.8
_model_state = {"loaded": False, "model": None, "path": None, "error": None}


def load_model(path):
    """Loads a scikit-learn pipeline saved with joblib. Only load files YOU created (pickle is not safe for untrusted files)."""
    import os
    _model_state.update(loaded=False, model=None, path=path, error=None)
    if not path or not os.path.isfile(path):
        return False
    try:
        import joblib
        model = joblib.load(path)
        if not hasattr(model, "predict_proba"):
            raise TypeError("model has no predict_proba")
        _model_state.update(loaded=True, model=model)
        return True
    except Exception as exc:  # fail safe: fall back to rules only
        _model_state["error"] = f"{type(exc).__name__}"
        return False


def model_loaded():
    return _model_state["loaded"]


def _ml(text):
    if not _model_state["loaded"]:
        return {"available": False, "note": "No trained ML model is loaded in this web app, so only rules ran. "
                "Train one in the Colab notebook and export it to enable the ML score."}
    try:
        classes = list(_model_state["model"].classes_)
        p = float(_model_state["model"].predict_proba([scam_rules_normalise(text)])[0][classes.index(1)])
    except Exception:
        return {"available": False, "note": "The ML model could not score this message, so only rules ran."}
    return {"available": True, "label": "scam-like" if p >= 0.5 else "not scam-like", "probability": round(p, 3),
            "note": "Model output on English SMS-style text. It is not an accuracy figure and can be wrong, "
                    "especially for Indian-style messages. It can never make a message 'High' on its own."}


def scam_rules_normalise(text):
    """Must stay identical to normalise() in the Colab notebook, because the exported model was trained on its output."""
    import re
    t = str(text).lower()
    t = re.sub(r"(https?://\S+|www\.\S+|\b[a-z0-9-]+\.(com|in|net|org|xyz|top|click|icu|ly)\b\S*)", " urltoken ", t)
    t = re.sub(r"\d+", " numtoken ", t)
    t = re.sub(r"[^a-z\s]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def analyse(text):
    res = scam_rules.analyse(text)
    ml = _ml(text)
    rule_category = res["category"]
    res["rule_category"] = rule_category
    res["ml"] = ml
    res["ml_raised_category"] = False
    if ml.get("available") and ml["probability"] >= ML_RAISE_THRESHOLD and rule_category in ("Low", "Inconclusive"):
        res["category"] = "Medium"          # ML can lift to Medium, never to High
        res["ml_raised_category"] = True
    res["method"] = {"type": "hybrid (rules decide; ML advisory)" if ml.get("available") else "rule-based",
                     "ml_or_llm_used": bool(ml.get("available")),
                     "summary": ("Keyword and pattern rules written by the team decide the category. " +
                                 ("A trained scikit-learn model adds an advisory score and can raise 'Low' to 'Medium' only. "
                                  if ml.get("available") else "No machine-learning model is loaded. ") +
                                 "No LLM reads your message. Text is not stored.")}
    return res
