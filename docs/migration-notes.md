# PredictCNC — Migration Notes & Technical Debt Resolution

## Legacy Audit Summary (C:\xampp\htdocs\PredictCNC)
The original project provided valuable domain logic and an attractive dark theme, but possessed critical issues:

1. **Plaintext Passwords**: Passwords in the users table had zero hashing.  
   *Resolution*: Implemented rgon2-cffi / passlib password hashing in new backend auth service.
2. **Missing Authorization Checks**: Historical logs (/history) had no login verification.  
   *Resolution*: Protected all operational routes using FastAPI Depends(get_current_user).
3. **State Mutation via HTTP GET**: Records could be deleted via simple GET links.  
   *Resolution*: Enforced standard RESTful HTTP methods (DELETE /api/v1/machines/{id}, DELETE /api/v1/history/{id}).
4. **Hardcoded Model Metrics**: eports.py returned fabricated 97.32% accuracy with 12,000 samples on a 10,000 row dataset.  
   *Resolution*: Created genuine ML evaluation script (ml/src/evaluate.py) computing real cross-validated metrics directly from the dataset.
5. **Collinear / Dead Feature**: load_density had 0 split gain across 200 trees in the LightGBM booster.  
   *Resolution*: Retained for backward compatibility with the existing serialized pickle, but flagged for removal in retraining.
6. **Feature Naming Mismatch**: Model was serialized with underscores (Rotational_speed_rpm) while Flask passed spaces (Rotational speed rpm).  
   *Resolution*: Canonical feature mapping dictionary in ml/src/inference.py ensures deterministic alignment.
7. **No Tenant Isolation**: All users viewed all machines regardless of company.  
   *Resolution*: Foreign key company_id on all entities ensures data boundaries.
